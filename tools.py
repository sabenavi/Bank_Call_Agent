#Simulacion de APIs del banco para consulta de saldo, tarjetas, etc.

def consultar_cuenta_api(cedula):
    saldo_simulado = 1250.40
    movimientos = [
        {"fecha": "2025-10-11", "detalle": "Depósito", "monto": 500.00},
        {"fecha": "2025-10-09", "detalle": "Pago tarjeta", "monto": -250.00},
    ]
    return saldo_simulado, movimientos


def consultar_tarjeta_api(cedula):
    tarjetas = [
        {"tarjeta": "AMEX", "limite": 3000.00, "disponible": 500.00},
        {"tarjeta": "VISA", "limite": 500.00, "disponible": 350.00},
    ]
    return tarjetas


def consultar_poliza_api(cedula):
    return {"tipo": "Seguro de vida", "vigencia": "hasta 2026-03-15", "estado": "Activa"}
