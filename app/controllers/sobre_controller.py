from app.controllers.licenca_controller import LicencaController
from app.controllers.seguranca_controller import SegurancaController
from app.services.sobre_service import coletar_informacoes, texto_para_suporte


class SobreController:
    """Leitura de informacoes do sistema. Aberta a qualquer usuario logado (nao expoe dados de negocio)."""

    def informacoes(self) -> dict:
        try:
            situacao = SegurancaController().situacao_backup()
        except Exception:  # noqa: BLE001 - a tela Sobre deve abrir mesmo com o banco indisponivel
            situacao = None
        info = coletar_informacoes(situacao)
        try:
            licenca = LicencaController()
            estado = licenca.situacao()
            info["licenca_titulo"] = estado.titulo
            info["licenca_detalhe"] = estado.detalhe
            info["licenca_estado"] = estado.estado
            info["licenca_erro"] = estado.erro
            info["licenca_dados"] = estado.licenca
            info["codigo_maquina"] = licenca.codigo_maquina()
        except Exception:  # noqa: BLE001 - nunca impede abrir a tela Sobre
            pass
        return info

    def ativar_licenca(self, caminho: str):
        """Valida e instala um arquivo .erplic. Levanta LicencaInvalida com a mensagem para o usuario."""
        return LicencaController().ativar(caminho)

    def texto_suporte(self) -> str:
        return texto_para_suporte(self.informacoes())
