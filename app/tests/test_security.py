from app.utils.security import gerar_hash_senha, verificar_senha


def test_hash_senha_nao_guarda_texto_puro():
    senha_hash = gerar_hash_senha("admin123")

    assert senha_hash != "admin123"
    assert verificar_senha("admin123", senha_hash)
    assert not verificar_senha("senha_errada", senha_hash)
