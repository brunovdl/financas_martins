"""
camera_price_scanner_modal.py — Scanner de etiqueta de gôndola zero-toque (DEC-026).

Implementa:
- Visor de câmera ao vivo com flet-camera (Camera control, validado via flet-mcp)
- Permissão de câmera via flet-permission-handler (PermissionHandler, Permission.CAMERA)
- Moldura de foco inteligente sobre a etiqueta com indicador de status
- Auto-captura periódica e processamento com Groq Vision (price_scanner_service)
- Feedback visual: moldura verde + vibração ao detectar preço com sucesso
- Fechamento automático e persistência imediata no item (zero toques adicionais)
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable

import flet as ft

from ui.components.modal_header import build_modal_header
from ui.theme import get_tokens, format_brl

logger = logging.getLogger(__name__)


def open_camera_price_scanner(
    page: ft.Page,
    item: dict[str, Any],
    theme_mode: str,
    on_price_detected: Callable[[str, float], None],
) -> None:
    """
    Abre o visor de câmera para escanear a etiqueta de gôndola de um item.
    Ao detectar o preço, chama on_price_detected(item_id, price) e fecha automaticamente.

    API validada via flet-mcp:
    - Camera(preview_enabled, content, on_state_change) — pacote flet-camera
    - Camera.initialize(description, resolution_preset) — async
    - Camera.take_picture() -> bytes — async
    - Camera.get_available_cameras() -> list[CameraDescription] — async
    - PermissionHandler.request(Permission.CAMERA) -> PermissionStatus — async
    - CameraLensDirection.BACK — traseira
    - ResolutionPreset.HIGH — resolução alta
    """
    T = get_tokens(theme_mode)
    item_id = str(item.get("id", ""))
    item_name = item.get("name", "Produto")

    dlg = ft.AlertDialog(modal=True)
    _scanning = {"active": True, "found": False}

    def close_dlg(_: Any = None) -> None:
        _scanning["active"] = False
        dlg.open = False
        if hasattr(page, "pop_dialog"):
            try:
                page.pop_dialog()
            except Exception:
                pass
        page.update()

    # Status label e moldura de foco
    status_text = ft.Text(
        "Aponte para a etiqueta de preço...",
        size=12,
        weight=ft.FontWeight.W_500,
        color=T["textMuted"],
        text_align=ft.TextAlign.CENTER,
    )

    frame_color_ref = {"color": T["accent"]}

    focus_frame = ft.Container(
        width=220,
        height=100,
        border=ft.Border.all(2.5, T["accent"]),
        border_radius=8,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    overlay_content = ft.Column(
        [
            ft.Container(expand=True),
            ft.Container(
                content=focus_frame,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Container(
                content=status_text,
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.only(top=8, bottom=12),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    # Câmera
    try:
        from flet_camera import Camera, CameraLensDirection, ResolutionPreset
    except ImportError:
        # Fallback: se flet-camera não está disponível (desktop), usa FilePicker
        _fallback_file_picker_scan(page, item, theme_mode, on_price_detected)
        return

    camera = Camera(
        expand=True,
        preview_enabled=True,
        content=overlay_content,
    )

    async def _init_camera():
        """Inicializa câmera traseira com resolução alta."""
        try:
            from flet_permission_handler import PermissionHandler, Permission, PermissionStatus

            ph = PermissionHandler()
            if hasattr(page, "services") and isinstance(page.services, list):
                if ph not in page.services:
                    page.services.append(ph)
                    page.update()

            perm_status = await ph.request(Permission.CAMERA)
            if perm_status != PermissionStatus.GRANTED:
                status_text.value = "⚠️ Permissão de câmera negada"
                status_text.color = T["danger"]
                page.update()
                return
        except ImportError:
            logger.debug("[Scanner] flet-permission-handler não disponível, tentando câmera diretamente.")
        except Exception as perm_err:
            logger.warning(f"[Scanner] Erro ao solicitar permissão de câmera: {perm_err}")

        try:
            # Registra câmera como serviço
            if hasattr(page, "services") and isinstance(page.services, list):
                if camera not in page.services:
                    page.services.append(camera)
                    page.update()

            cameras = await camera.get_available_cameras()
            back_camera = None
            for cam in cameras:
                if cam.lens_direction == CameraLensDirection.BACK:
                    back_camera = cam
                    break
            if not back_camera and cameras:
                back_camera = cameras[0]

            if back_camera:
                await camera.initialize(
                    description=back_camera,
                    resolution_preset=ResolutionPreset.HIGH,
                )
                # Inicia auto-captura periódica
                _start_auto_capture(camera, page)
            else:
                status_text.value = "⚠️ Nenhuma câmera encontrada"
                status_text.color = T["danger"]
                page.update()
        except Exception as cam_err:
            logger.error(f"[Scanner] Erro ao inicializar câmera: {cam_err}")
            status_text.value = f"⚠️ Erro na câmera: {cam_err}"
            status_text.color = T["danger"]
            page.update()

    _is_capturing = {"active": False}

    def _trigger_capture() -> None:
        """Dispara captura e análise da imagem (acionado por auto-loop ou botão manual)."""
        if not _scanning["active"] or _scanning["found"] or _is_capturing["active"]:
            return
        _is_capturing["active"] = True

        async def _do_capture():
            try:
                status_text.value = "🔍 Analisando etiqueta..."
                status_text.color = T["accent"]
                status_text.weight = ft.FontWeight.BOLD
                try:
                    page.update()
                except Exception:
                    pass

                image_bytes = await camera.take_picture()
                if image_bytes and _scanning["active"]:
                    _process_captured_image(image_bytes, page)
                else:
                    _is_capturing["active"] = False
                    status_text.value = "Aponte para a etiqueta de preço..."
                    status_text.color = T["textMuted"]
                    status_text.weight = ft.FontWeight.W_500
                    try:
                        page.update()
                    except Exception:
                        pass
            except Exception as cap_err:
                logger.debug(f"[Scanner] Erro na captura: {cap_err}")
                _is_capturing["active"] = False
                status_text.value = "Aponte para a etiqueta de preço..."
                status_text.color = T["textMuted"]
                status_text.weight = ft.FontWeight.W_500
                try:
                    page.update()
                except Exception:
                    pass

        if hasattr(page, "run_task"):
            page.run_task(_do_capture)
        else:
            _is_capturing["active"] = False

    def _start_auto_capture(cam_ctrl, pg):
        """Inicia thread de auto-captura contínua a cada 1.8 segundos para leitura da etiqueta."""
        def _auto_loop():
            import time
            time.sleep(1.2)  # Aguarda estabilização da câmera
            while _scanning["active"] and not _scanning["found"]:
                if not _is_capturing["active"]:
                    _trigger_capture()
                time.sleep(1.8)

        threading.Thread(target=_auto_loop, daemon=True).start()

    def _process_captured_image(image_bytes: bytes, pg):
        """Processa imagem capturada com Groq Vision em background."""
        from services.price_scanner_service import extract_price_from_image_bytes

        def _worker():
            if not _scanning["active"] or _scanning["found"]:
                _is_capturing["active"] = False
                return
            result = extract_price_from_image_bytes(image_bytes, item_name=item_name)

            def _handle_result():
                if not _scanning["active"] or _scanning["found"]:
                    _is_capturing["active"] = False
                    return

                if result.get("success") and result.get("price") is not None:
                    _scanning["found"] = True
                    detected_price = float(result["price"])

                    # Feedback visual: moldura verde + texto de sucesso
                    focus_frame.border = ft.Border.all(3, T["success"])
                    status_text.value = f"✅ {format_brl(detected_price)} detectado!"
                    status_text.color = T["success"]
                    status_text.weight = ft.FontWeight.BOLD
                    try:
                        pg.update()
                    except Exception:
                        pass

                    # Vibração háptica
                    try:
                        from flet import HapticFeedback
                        haptic = HapticFeedback()
                        if hasattr(pg, "services") and isinstance(pg.services, list):
                            if haptic not in pg.services:
                                pg.services.append(haptic)
                        if hasattr(pg, "run_task"):
                            pg.run_task(haptic.vibrate)
                    except Exception:
                        pass

                    # Fecha e aplica após breve delay visual
                    import time

                    def _close_and_apply():
                        time.sleep(0.6)

                        def _finalize():
                            close_dlg()
                            on_price_detected(item_id, detected_price)

                        if hasattr(pg, "run_thread"):
                            pg.run_thread(_finalize)
                        else:
                            _finalize()

                    threading.Thread(target=_close_and_apply, daemon=True).start()
                else:
                    _is_capturing["active"] = False
                    status_text.value = "Ajuste o foco sobre a etiqueta..."
                    status_text.color = T["textMuted"]
                    status_text.weight = ft.FontWeight.W_500
                    try:
                        pg.update()
                    except Exception:
                        pass

            if hasattr(pg, "run_thread"):
                pg.run_thread(_handle_result)
            else:
                _handle_result()

        threading.Thread(target=_worker, daemon=True).start()

    # Montagem do diálogo
    dlg_header = build_modal_header(
        title=f"Escanear: {item_name}",
        on_close=close_dlg,
        theme_tokens=T,
    )

    camera_container = ft.Container(
        content=camera,
        width=340,
        height=280,
        border_radius=12,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    btn_scan_manual = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, size=16, color="#08090F"),
                ft.Text("Ler Etiqueta Agora", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        ),
        style=ft.ButtonStyle(
            bgcolor=T["accent"],
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        ),
        height=38,
        on_click=lambda _: _trigger_capture(),
    )

    dlg_body = ft.Container(
        content=ft.Column(
            [
                camera_container,
                ft.Container(
                    content=ft.Text(
                        "Posicione a etiqueta dentro da moldura",
                        size=11,
                        color=T["textMuted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.only(top=2, bottom=4),
                ),
                btn_scan_manual,
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        padding=ft.Padding.all(12),
        bgcolor=T["surface"],
        border_radius=12,
    )

    dlg.title = dlg_header
    dlg.content = dlg_body
    dlg.actions = [
        ft.Button(
            content=ft.Text("Cancelar", color=T["textMuted"], size=12),
            on_click=close_dlg,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
    ]
    dlg.bgcolor = T["surface"]
    dlg.shape = ft.RoundedRectangleBorder(radius=12)

    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()

    # Inicia a câmera após abrir o diálogo
    if hasattr(page, "run_task"):
        page.run_task(_init_camera)


def _fallback_file_picker_scan(
    page: ft.Page,
    item: dict[str, Any],
    theme_mode: str,
    on_price_detected: Callable[[str, float], None],
) -> None:
    """
    Fallback para ambientes sem flet-camera: usa FilePicker para selecionar foto da etiqueta.
    """
    from services.price_scanner_service import extract_price_from_file_path, extract_price_from_base64

    T = get_tokens(theme_mode)
    item_id = str(item.get("id", ""))
    item_name = item.get("name", "Produto")

    async def _pick_and_scan():
        fp = ft.FilePicker()
        if hasattr(page, "services") and isinstance(page.services, list):
            if fp not in page.services:
                page.services.append(fp)

        try:
            files = await fp.pick_files(
                dialog_title=f"Fotografar Etiqueta: {item_name}",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False,
            )
            if not files:
                return

            picked_file = files[0]

            # Feedback imediato de leitura
            loading_snack = ft.SnackBar(
                content=ft.Row(
                    [
                        ft.ProgressRing(width=16, height=16, stroke_width=2, color="#08090F"),
                        ft.Text(f"Analisando etiqueta de {item_name}...", color="#08090F", weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                bgcolor=T["accent"],
                duration=4000,
            )
            page.snack_bar = loading_snack
            loading_snack.open = True
            page.update()

            def _process():
                import base64
                res: dict[str, Any] = {"success": False}
                try:
                    if getattr(picked_file, "path", None):
                        res = extract_price_from_file_path(picked_file.path, item_name=item_name)
                    elif getattr(picked_file, "bytes", None):
                        b64 = base64.b64encode(picked_file.bytes).decode("utf-8")
                        res = extract_price_from_base64(b64, item_name=item_name)
                except Exception as ex:
                    res = {"success": False, "error": str(ex)}

                def _update():
                    if res.get("success") and res.get("price") is not None:
                        detected_val = float(res["price"])
                        on_price_detected(item_id, detected_val)
                        snack = ft.SnackBar(
                            content=ft.Text(
                                f"✅ {item_name}: {format_brl(detected_val)} detectado!",
                                color="#08090F",
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=T["success"],
                            duration=3500,
                        )
                        page.snack_bar = snack
                        snack.open = True
                        page.update()
                    else:
                        err_msg = res.get("error") or "Preço não identificado na foto"
                        snack = ft.SnackBar(
                            content=ft.Text(f"⚠️ {err_msg}", color="#08090F", weight=ft.FontWeight.BOLD),
                            bgcolor=T["warning"],
                            duration=3500,
                        )
                        page.snack_bar = snack
                        snack.open = True
                        page.update()

                if hasattr(page, "run_thread"):
                    page.run_thread(_update)
                else:
                    _update()

            threading.Thread(target=_process, daemon=True).start()
        except Exception as ex:
            snack = ft.SnackBar(
                content=ft.Text(f"Erro: {ex}", color="#08090F"),
                bgcolor=T["danger"],
                duration=3000,
            )
            page.snack_bar = snack
            snack.open = True
            page.update()

    if hasattr(page, "run_task"):
        page.run_task(_pick_and_scan)
