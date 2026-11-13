from app.controllers.seguranca_controller import SegurancaController
from app.services.sobre_service import coletar_informacoes, texto_para_suporte


class SobreController:
    """Leitura de informacoes do sistema. Aberta a qualquer usuario logado (nao expoe dados de negocio)."""

    def informacoes(self) -> dict:
        try:
            situacao = SegurancaController().situacao_backup()
        except Exception:  # noqa: BLE001 - a tela Sobre deve abrir mesmo com o banco indisponivel
            situacao = None
        return coletar_informacoes(situacao)

    def texto_suporte(self) -> str:
        return texto_para_suporte(self.informacoes())
