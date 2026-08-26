# ui/qr_dialog.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0

import flet as ft
from core.i18n import i18n
import qrcode
import io
import base64

def generate_qr_base64(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def show_qr_dialog(page: ft.Page, get_color, ip_address: str, port: int):
    """Muestra un diálogo con el código QR para conectarse a la IP"""
    url = f"http://{ip_address}:{port}"
    qr_base64 = generate_qr_base64(url)
    
    dialog = ft.AlertDialog(
        modal=False,
        title=ft.Row(
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, color=get_color("accent")),
                ft.Text(i18n.get("dialog_qr_title"), size=20, weight=ft.FontWeight.BOLD, color=get_color("text_primary")),
            ]
        ),
        content=ft.Container(
            width=350,
            padding=10,
            content=ft.Column(
                tight=True,
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        i18n.get("dialog_qr_instructions"),
                        size=14,
                        color=get_color("text_secondary"),
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        padding=10,
                        border_radius=10,
                        content=ft.Image(
                            src=f"data:image/png;base64,{qr_base64}",
                            width=250,
                            height=250,
                        )
                    ),
                    ft.Text(
                        url,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=get_color("accent"),
                        text_align=ft.TextAlign.CENTER
                    )
                ]
            )
        ),
        actions=[
            ft.TextButton(
                i18n.get("close"),
                on_click=lambda e: close_dialog(),
                style=ft.ButtonStyle(color=get_color("accent"))
            )
        ],
        actions_padding=ft.padding.Padding(left=0, right=10, top=0, bottom=10),
        shape=ft.RoundedRectangleBorder(radius=12),
        bgcolor=get_color("bg_card"),
    )
    
    def close_dialog():
        page.pop_dialog()

    page.show_dialog(dialog)
