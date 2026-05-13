from src.common.application.ports.email_notifier import IEmailNotifier


class WellcomeEmailService:
    def __init__(self, notifier: IEmailNotifier):
        self.notifier = notifier

    def build_body(self, url: str) -> str:
        body = f"""
        Bienvenido a El Rodeo!

        Hace click en el siguiente enlace para comenzar:
        {url}
        """
        return body

    def send(
        self,
        to: list[str],
        subject: str,
        redirect_url: str,
    ) -> None:
        body = self.build_body(redirect_url)
        self.notifier.send(to, subject, body)
