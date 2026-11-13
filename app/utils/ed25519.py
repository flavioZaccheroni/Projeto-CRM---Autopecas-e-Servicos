"""Ed25519 (RFC 8032) em Python puro: assinatura e verificacao sem dependencias externas.

Usado para o arquivo de licenca: o app so VERIFICA (chave publica embutida); a assinatura e feita
pelo script do fornecedor (scripts/gerar_licenca.py) com a chave privada, que nunca vai no app.
Implementacao de referencia (nao resistente a ataques de canal lateral: nao use para segredos em servidores).
"""

from __future__ import annotations

import hashlib

_P = 2**255 - 19
_D = -121665 * pow(121666, _P - 2, _P) % _P
_Q = 2**252 + 27742317777372353535851937790883648493
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)


def _sha512(dados: bytes) -> bytes:
    return hashlib.sha512(dados).digest()


def _sha512_modq(dados: bytes) -> int:
    return int.from_bytes(_sha512(dados), "little") % _Q


def _inv(x: int) -> int:
    return pow(x, _P - 2, _P)


def _somar(a, b):
    A = (a[1] - a[0]) * (b[1] - b[0]) % _P
    B = (a[1] + a[0]) * (b[1] + b[0]) % _P
    C = 2 * a[3] * b[3] * _D % _P
    D = 2 * a[2] * b[2] % _P
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _P, G * H % _P, F * G % _P, E * H % _P)


def _multiplicar(escalar: int, ponto):
    resultado = (0, 1, 1, 0)
    while escalar > 0:
        if escalar & 1:
            resultado = _somar(resultado, ponto)
        ponto = _somar(ponto, ponto)
        escalar >>= 1
    return resultado


def _iguais(a, b) -> bool:
    if (a[0] * b[2] - b[0] * a[2]) % _P != 0:
        return False
    return (a[1] * b[2] - b[1] * a[2]) % _P == 0


def _recuperar_x(y: int, sinal: int):
    if y >= _P:
        return None
    x2 = (y * y - 1) * _inv(_D * y * y + 1)
    if x2 == 0:
        return None if sinal else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = x * _SQRT_M1 % _P
    if (x * x - x2) % _P != 0:
        return None
    if (x & 1) != sinal:
        x = _P - x
    return x


_GY = 4 * _inv(5) % _P
_GX = _recuperar_x(_GY, 0)
_BASE = (_GX, _GY, 1, _GX * _GY % _P)


def _comprimir(ponto) -> bytes:
    zinv = _inv(ponto[2])
    x, y = ponto[0] * zinv % _P, ponto[1] * zinv % _P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _descomprimir(dados: bytes):
    y = int.from_bytes(dados, "little")
    sinal = y >> 255
    y &= (1 << 255) - 1
    x = _recuperar_x(y, sinal)
    if x is None:
        return None
    return (x, y, 1, x * y % _P)


def _expandir(segredo: bytes) -> tuple[int, bytes]:
    h = _sha512(segredo)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def chave_publica(segredo: bytes) -> bytes:
    """Chave publica (32 bytes) a partir da chave privada (semente de 32 bytes)."""
    if len(segredo) != 32:
        raise ValueError("A chave privada deve ter 32 bytes.")
    a, _ = _expandir(segredo)
    return _comprimir(_multiplicar(a, _BASE))


def assinar(segredo: bytes, mensagem: bytes) -> bytes:
    if len(segredo) != 32:
        raise ValueError("A chave privada deve ter 32 bytes.")
    a, prefixo = _expandir(segredo)
    publica = _comprimir(_multiplicar(a, _BASE))
    r = _sha512_modq(prefixo + mensagem)
    R = _comprimir(_multiplicar(r, _BASE))
    h = _sha512_modq(R + publica + mensagem)
    s = (r + h * a) % _Q
    return R + int.to_bytes(s, 32, "little")


def verificar(publica: bytes, mensagem: bytes, assinatura: bytes) -> bool:
    """True so se a assinatura for valida para a mensagem e a chave publica. Entradas ruins devolvem False."""
    if len(publica) != 32 or len(assinatura) != 64:
        return False
    A = _descomprimir(publica)
    if A is None:
        return False
    Rs = assinatura[:32]
    R = _descomprimir(Rs)
    if R is None:
        return False
    s = int.from_bytes(assinatura[32:], "little")
    if s >= _Q:
        return False
    h = _sha512_modq(Rs + publica + mensagem)
    return _iguais(_multiplicar(s, _BASE), _somar(R, _multiplicar(h, A)))
