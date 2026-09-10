"""
core/notifier.py - Notificaciones toast nativas de Windows.

Genera un toast via Windows.UI.Notifications (PowerShell) sin
dependencias externas. Fallback silencioso si falla.
"""

import subprocess
import sys


def _ps_quote(text: str) -> str:
    """Escapa texto para interpolarlo como string en PowerShell."""
    return "'" + text.replace("'", "''") + "'"


def notify(title: str, message: str) -> None:
    """
    Muestra una notificacion toast de Windows.

    Parameters
    ----------
    title : titulo de la notificacion (ej: "J.A.R.V.I.S.").
    message : cuerpo de la notificacion.
    """
    if sys.platform != "win32":
        return

    title_q = _ps_quote(title)
    msg_q = _ps_quote(message)

    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, "
        "Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, "
        "ContentType = WindowsRuntime] | Out-Null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]"
        "::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$textNodes = $template.GetElementsByTagName('text'); "
        f"$textNodes.Item(0).AppendChild($template.CreateTextNode({title_q})) | Out-Null; "
        f"$textNodes.Item(1).AppendChild($template.CreateTextNode({msg_q})) | Out-Null; "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
        "[Windows.UI.Notifications.ToastNotificationManager]"
        "::CreateToastNotifier('JARVIS').Show($toast)"
    )

    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-STA", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except OSError:  # pragma: no cover
        pass