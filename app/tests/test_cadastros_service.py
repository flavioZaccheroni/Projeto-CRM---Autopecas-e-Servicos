import pytest

from app.repositories.cadastro_repository import ClienteRepository
from app.services.cadastro_service import ClienteService


def test_cliente_nao_permite_cpf_cnpj_duplicado(session):
    service = ClienteService(ClienteRepository(session))
    service.salvar(
        {
            "nome": "Cliente A",
            "tipo_pessoa": "PF",
            "cpf_cnpj": "123",
            "telefone": "",
            "email": "",
            "ativo": True,
        }
    )

    with pytest.raises(ValueError, match="CPF/CNPJ"):
        service.salvar(
            {
                "nome": "Cliente B",
                "tipo_pessoa": "PF",
                "cpf_cnpj": "123",
                "telefone": "",
                "email": "",
                "ativo": True,
            }
        )
