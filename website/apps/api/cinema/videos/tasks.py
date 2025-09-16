import json
import logging
import secrets
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from library.aws.client.s3 import S3UploadClient
from utils.posix import posix_join

from apps.api.cinema.audio_tracks.models import AudioTrack
from apps.api.cinema.videos.models import Video, VideoResolution
from apps.api.cinema.videos.services.video_status_service import VideoStatusService
from apps.core.models import Language


@dataclass(frozen=True)
class Rendition:
    name: str
    width: int
    height: int
    maxrate_k: int
    bufsize_k: int


RENDITIONS: list[Rendition] = [
    Rendition("360p",  640,  360,  856,  1200),
    Rendition("480p",  842,  480, 1498,  2100),
    Rendition("720p", 1280,  720, 2996,  4200),
    Rendition("1080p",1920, 1080, 5350,  7500),
]

VIDEO_CODEC_ARGS = [
    "-c:v", "h264",
    "-profile:v", "main",
    "-crf", "20",
    "-preset", "veryfast",
    "-sc_threshold", "0",
    "-g", "48",
    "-keyint_min", "48",
]

AUDIO_CODEC_ARGS = [
    "-c:a", "aac",
    "-ar", "48000",
    "-ac", "2",
    "-b:a", "128k",
]

HLS_ARGS = [
    "-hls_time", "6",
    "-hls_flags", "independent_segments",
    "-hls_playlist_type", "vod",
]

FFMPEG_COMMON_ARGS = [
    "-hide_banner",
    "-fflags", "+genpts",
]

BUCKET = settings.AWS_STORAGE_BUCKET_NAME
HLS_BASE = "hls"


def run_cmd(args: list[str]) -> subprocess.CompletedProcess:
    """Запустить внешнюю команду без shell. Логируем при ошибках."""
    logging.debug("Run: %s", " ".join(args))
    return subprocess.run(args, check=True, capture_output=True, text=True)


def ffprobe_json(path: Path) -> dict:
    """Безопасный ffprobe в JSON."""
    args = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    cp = run_cmd(args)
    data = json.loads(cp.stdout or "{}")
    # при желании можно фильтровать по select, но оставим полный JSON — полезно для дебага
    return data


def get_video_duration_seconds(path: Path) -> float:
    data = ffprobe_json(path)
    try:
        return float(data.get("format", {}).get("duration", 0.0))
    except (TypeError, ValueError):
        return 0.0


def has_audio_stream(path: Path) -> bool:
    data = ffprobe_json(path)
    for st in data.get("streams", []):
        if st.get("codec_type") == "audio":
            return True
    return False


@dataclass
class AudioSource:
    is_builtin: bool
    language_code: str  # ISO, e.g. 'en', 'ru', 'und'
    is_default: bool
    tmp_path: Path | None  # None для встроенной дорожки


def build_var_stream_map(renditions: list[Rendition], audio_sources: list[AudioSource]) -> str:
    """
    Формируем var_stream_map для HLS:
    - сначала все видеорендеры, подключённые к общей группе аудио agroup:aud
    - затем каждая аудиодорожка с language/name, ровно одна default:yes
    """
    parts: list[str] = []
    for idx, r in enumerate(renditions):
        parts.append(f"v:{idx},agroup:aud,name:{r.name}")

    default_given = False
    for i, a in enumerate(audio_sources):
        p = f"a:{i},agroup:aud,language:{a.language_code},name:language-{a.language_code}"
        if a.is_default and not default_given:
            p += ",default:yes"
            default_given = True
        parts.append(p)

    # если не было ни одной default=true — пометим первую, чтобы HLS-плееры не выпадали
    if audio_sources and not default_given:
        # заменить у первой аудио-строки добавлением default:yes
        i = len(renditions)  # индекс первой аудио-строки в parts
        parts[i] = parts[i] + ",default:yes"

    return " ".join(parts)


def ffmpeg_build_command(
    local_src: Path,
    audio_files: list[Path],
    out_dir: Path,
    renditions: list[Rendition],
    audio_sources: list[AudioSource],
    hls_keyinfo_path: Path,
    master_name: str,
) -> list[str]:
    """
    Строим аргументы ffmpeg (без shell), с:
    - входами: 1 видео + N внешних аудио
    - 1 видеофильтр scale на каждый rendition
    - аудио-graph apad/atrim под длительность исходника
    - корректным var_stream_map + шаблонами имен
    """
    duration = get_video_duration_seconds(local_src)

    args: list[str] = ["ffmpeg", *FFMPEG_COMMON_ARGS]

    # inputs
    args += ["-i", str(local_src)]
    for f in audio_files:
        args += ["-i", str(f)]

    # video mapping (по числу rendition'ов)
    for _ in renditions:
        args += ["-map", "0:v"]

    # построим filter_complex для аудио (apad/atrim)
    filter_parts: list[str] = []
    next_ext_input_idx = 1  # индексация внешних аудио начинается с 1 (после видео 0)
    audio_out_labels: list[str] = []
    for i, src in enumerate(audio_sources):
        in_spec = "0:a" if src.is_builtin else f"{next_ext_input_idx}:a"
        if not src.is_builtin:
            next_ext_input_idx += 1
        out_lbl = f"a{i}p"
        filter_parts.append(
            f"[{in_spec}]apad=pad_dur={duration},atrim=end={duration},asetpts=PTS-STARTPTS[{out_lbl}]"
        )
        audio_out_labels.append(out_lbl)

    if filter_parts:
        args += ["-filter_complex", ";".join(filter_parts)]
        # аудио-мэппинг из фильтра
        for lbl in audio_out_labels:
            args += ["-map", f"[{lbl}]"]

    # кодеки (общие)
    args += VIDEO_CODEC_ARGS
    args += AUDIO_CODEC_ARGS

    # видео-фильтры и битрейты под каждый rendition
    for idx, r in enumerate(renditions):
        args += [
            f"-filter:v:{idx}",
            f"scale=w={r.width}:h={r.height}:force_original_aspect_ratio=decrease",
            f"-maxrate:v:{idx}", f"{r.maxrate_k}k",
            f"-bufsize:v:{idx}", f"{r.bufsize_k}k",
        ]

    # var_stream_map
    var_stream_map = build_var_stream_map(renditions, audio_sources)
    args += ["-var_stream_map", var_stream_map]

    # HLS
    seg_tmpl = str(out_dir / "%v_%03d.ts")
    var_pl_tmpl = str(out_dir / "%v.m3u8")
    args += ["-hls_key_info_file", str(hls_keyinfo_path)]
    args += HLS_ARGS
    args += ["-master_pl_name", master_name]
    args += ["-hls_segment_filename", seg_tmpl, var_pl_tmpl]

    return args


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def create_master_playlist(self, base_url: str, video_id: int):
    """
    Генерим HLS-мастер и вариативные плейлисты с несколькими аудиодорожками.
    Паблишим в S3 под версионированной директорией build_id.
    """
    try:
        video = Video.objects.select_related("file", "original_language").get(id=video_id)
    except ObjectDoesNotExist:
        logging.error("Video %s not found", video_id)
        return

    VideoStatusService.processing(video)

    upload_client = S3UploadClient()
    build_id = timezone.now().strftime("%d-%m-%Y-%H-%M-%S")

    # S3 ключи (POSIX!)
    hls_key_s3_key = posix_join(HLS_BASE, "keys", str(video.id), "hls.key")
    hls_video_prefix = posix_join(HLS_BASE, "videos", str(video.id))
    # подчистим старые сборки для этого видео
    try:
        upload_client.delete_prefix(hls_video_prefix)
    except Exception as e:
        # не фатально: продолжим, новая сборка будет в подпапке build_id
        logging.warning("Failed to clean S3 prefix %s: %s", hls_video_prefix, e)

    hls_build_prefix = posix_join(hls_video_prefix, build_id)

    try:
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)

            src_key = str(video.file.file)
            local_src = tmpdir / Path(src_key).name
            upload_client.download_to(src_key, local_src)

            # папка результатов
            out_dir = tmpdir / local_src.stem
            out_dir.mkdir(parents=True, exist_ok=True)

            # --- HLS ключ и keyinfo ---
            key_bytes = secrets.token_bytes(16)         # AES-128
            iv_hex = secrets.token_hex(16)              # 16 байт -> 32 hex-символа
            key_filename = "decrypt.key"
            key_local_path = out_dir / key_filename
            key_local_path.write_bytes(key_bytes)

            # публичный (или полу-публичный) URL до key endpoint
            key_public_local_url = reverse("api:cinema:videos:hls-key", kwargs={"pk": video.id})
            key_public_url = (base_url.rstrip("/") + key_public_local_url)

            hls_keyinfo_path = out_dir / "hls.keyinfo"
            hls_keyinfo_path.write_text("\n".join([key_public_url, str(key_local_path), iv_hex]), encoding="utf-8")

            # --- аудио-источники ---
            audio_sources: list[AudioSource] = []
            audio_files: list[Path] = []

            builtin_audio = has_audio_stream(local_src)
            if builtin_audio and video.original_language:
                lang_code = video.original_language.code
                # Создадим/обновим дефолтную аудиодорожку под оригинал
                try:
                    AudioTrack.objects.get_or_create(
                        video=video,
                        language=video.original_language,
                        defaults={"is_default": True} if video.original_language else {},
                    )
                except Exception as e:
                    logging.warning("AudioTrack get_or_create failed: %s", e)

                audio_sources.append(
                    AudioSource(
                        is_builtin=True,
                        language_code=lang_code,
                        is_default=bool(video.original_language),
                        tmp_path=None,
                    )
                )

            # внешние аудиодорожки (от дефолтных к остальным)
            ext_qs = (
                video.audio_tracks.select_related("file", "language")
                .filter(file__isnull=False)
                .order_by("-is_default", "id")
            )
            for at in ext_qs:
                s3_key = str(at.file.file)
                local_audio = tmpdir / Path(getattr(at.file, "file_name", Path(s3_key).name)).name
                upload_client.download_to(s3_key, local_audio)
                audio_files.append(local_audio)
                audio_sources.append(
                    AudioSource(
                        is_builtin=False,
                        language_code=at.language.code if at.language else "und",
                        is_default=bool(at.is_default),
                        tmp_path=local_audio,
                    )
                )

            # --- ffmpeg ---
            master_name = "master.m3u8"
            ffmpeg_args = ffmpeg_build_command(
                local_src=local_src,
                audio_files=audio_files,
                out_dir=out_dir,
                renditions=RENDITIONS,
                audio_sources=audio_sources,
                hls_keyinfo_path=hls_keyinfo_path,
                master_name=master_name,
            )
            try:
                # если ffmpeg отвалится — дадим Celery шанс на retry
                run_cmd(ffmpeg_args)
            except subprocess.CalledProcessError as e:
                logging.error("ffmpeg failed: %s\nstdout:\n%s\nstderr:\n%s", e, e.stdout, e.stderr)
                raise self.retry(exc=e) from e

            # --- публикация результатов в S3 ---
            # 1) .ts
            for ts in sorted(out_dir.glob("*.ts")):
                upload_client.upload_file(posix_join(hls_build_prefix, ts.name), ts)

            # 2) аудио-плейлисты language-*.m3u8 + синхронизация с AudioTrack
            for pl in out_dir.glob("language-*.m3u8"):
                lang_code = pl.stem.split("-", 1)[-1]
                lang: Language | None = Language.objects.filter(code__iexact=lang_code).first()
                if lang is None:
                    logging.warning("Unknown language code from playlist: %s", lang_code)
                else:
                    AudioTrack.objects.update_or_create(
                        video=video,
                        language=lang,
                        defaults={
                            "hls_file": posix_join(hls_build_prefix, pl.name),
                        },
                    )
                upload_client.upload_file(posix_join(hls_build_prefix, pl.name), pl)

            # 3) вариативные видео-плейлисты %v.m3u8
            variant_playlists = sorted(out_dir.glob("[0-9]*.m3u8"))
            for pl in variant_playlists:
                upload_client.upload_file(posix_join(hls_build_prefix, pl.name), pl)

            # 4) мастер и ключ
            master_path = out_dir / master_name
            upload_client.upload_file(posix_join(hls_build_prefix, master_name), master_path)
            upload_client.upload_file(hls_key_s3_key, key_local_path)

            # 5) сведения о доступных разрешениях
            # маппинг индекса плейлиста на «360/480/720/1080»
            with transaction.atomic():
                for idx, pl in enumerate(variant_playlists):
                    if idx < len(RENDITIONS):
                        res_short = RENDITIONS[idx].name.replace("p", "")  # "360" из "360p"
                        VideoResolution.objects.update_or_create(
                            video=video,
                            resolution=res_short,
                            defaults={"file": posix_join(hls_build_prefix, pl.name)},
                        )

                # обновим сам Video
                video.hls_master_playlist = posix_join(hls_build_prefix, master_name)
                video.hls_decrypt_key = hls_key_s3_key
                video.save()

    except Exception as e:
        logging.exception("create_master_playlist failed for video %s: %s", video_id, e)
        try:
            VideoStatusService.failed(video)
        except Exception:  # если video не загрузился — пропустим
            pass
        # дайте Celery возможность ретраить по общим ошибкам тоже
        raise self.retry(exc=e) from e

    # финал
    try:
        VideoStatusService.completed(video)
    except Exception as e:
        logging.warning("VideoStatusService.completed failed: %s", e)
