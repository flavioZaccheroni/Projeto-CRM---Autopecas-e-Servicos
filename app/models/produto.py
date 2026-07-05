from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias_produto.id"))
    marca_id: Mapped[int | None] = mapped_column(ForeignKey("marcas_produto.id"))
    ncm: Mapped[str | None] = mapped_column(String(20))
    unidade: Mapped[str] = mapped_column(String(10), default="UN", nullable=False)
    preco_custo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    estoque_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    categoria = relationship("CategoriaProduto", back_populates="produtos")
    marca = relationship("MarcaProduto", back_populates="produtos")
    estoque = relationship("Estoque", back_populates="produto", uselist=False)
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="produto")

    def __str__(self) -> str:
        return f"{self.codigo} - {self.descricao}"
