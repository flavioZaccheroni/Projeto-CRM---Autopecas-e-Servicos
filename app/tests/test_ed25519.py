import pytest

from app.utils import ed25519

# Vetores de teste do RFC 8032, secao 7.1
VETORES = [
    (
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "",
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
    ),
    (
        "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "72",
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
    ),
]


@pytest.mark.parametrize(("segredo", "publica", "mensagem", "assinatura"), VETORES)
def test_vetores_do_rfc_8032(segredo, publica, mensagem, assinatura):
    segredo_b, publica_b, mensagem_b = bytes.fromhex(segredo), bytes.fromhex(publica), bytes.fromhex(mensagem)
    assert ed25519.chave_publica(segredo_b) == publica_b
    assert ed25519.assinar(segredo_b, mensagem_b).hex() == assinatura
    assert ed25519.verificar(publica_b, mensagem_b, bytes.fromhex(assinatura)) is True


def test_adulteracao_e_entradas_invalidas_sao_rejeitadas():
    segredo = bytes(range(32))
    publica = ed25519.chave_publica(segredo)
    assinatura = ed25519.assinar(segredo, b"licenca")
    assert ed25519.verificar(publica, b"licenca", assinatura)
    assert not ed25519.verificar(publica, b"licenca2", assinatura)
    assert not ed25519.verificar(ed25519.chave_publica(bytes(32)), b"licenca", assinatura)
    ruim = bytearray(assinatura)
    ruim[10] ^= 1
    assert not ed25519.verificar(publica, b"licenca", bytes(ruim))
    assert not ed25519.verificar(publica, b"licenca", assinatura[:-1])
    assert not ed25519.verificar(b"curta", b"licenca", assinatura)
    assert not ed25519.verificar(publica, b"licenca", b"\xff" * 64)
