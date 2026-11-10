import numpy as np

import cronico as C


def test_maior_sequencia():
    fora = np.array([[1, 1, 0, 1, 1, 1, 0], [0, 0, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1]], dtype=bool)
    assert list(C.maior_sequencia(fora)) == [3, 0, 7]


def test_regra_e_ou_de_percentual_e_sequencia():
    d = 60
    v = np.full((3, d), 99.0)
    v[0, ::2] = 90.0                 # 50% dos dias fora, alternados -> crônico pelo percentual, sem sequência
    v[1, 10:24] = 90.0               # 14 dias seguidos fora, 23% do total -> crônico pela sequência
    v[2, ::10] = 90.0                # 6 dias isolados -> não é crônico
    e = C.etiquetas(v)
    assert list(e["regra_completa"]) == [True, True, False]
    assert list(e["so_percentual"]) == [True, False, False]
    assert list(e["so_sequencia"]) == [False, True, False]


def test_ruido_estacionario_tem_o_desvio_pedido():
    rng = np.random.default_rng(0)
    v = C.simular(rng, np.zeros(20000), 5, phi=0.9)
    assert abs(v.std() - C.SIGMA) < 0.05
    assert abs(v.mean() - C.META) < 0.05


def test_celula_longe_da_meta_nao_troca_de_etiqueta():
    df = C.rodar(0)
    longe = df[df["m_sigma"].abs() > 1.5]
    assert (longe["regra_completa_A"] == longe["regra_completa_B"]).all()
    assert (longe["regra_completa_A"] == longe["real_cronica"]).all()
