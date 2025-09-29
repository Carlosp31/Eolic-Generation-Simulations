import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from py_wake.site import XRSite
from py_wake import BastankhahGaussian
from py_wake.wind_turbines import WindTurbines
from py_wake.wind_turbines.power_ct_functions import PowerCtTabular

def crear_site_offshore_con_weibull():
    """Crear sitio offshore con parámetros Weibull correctos"""
    
    wd = np.arange(0, 360, 10)  # Direcciones de 0 a 350 grados
    ws = np.arange(3, 25, 1)    # Velocidades de 3 a 24 m/s
    
    print(f"Configurando {len(wd)} direcciones y {len(ws)} velocidades de viento")
    
    # Parámetros Weibull
    A_values = 9.0 + 1.5 * np.cos(np.deg2rad(wd - 180))
    k_values = 2.1 + 0.1 * np.sin(np.deg2rad(wd))
    
    # Frecuencia por sector
    sector_freq = np.exp(-0.5 * ((wd - 270) / 60) ** 2)
    sector_freq = sector_freq / sector_freq.sum()
    
    # Crear arrays 2D
    A_2d = np.tile(A_values, (len(ws), 1)).T
    k_2d = np.tile(k_values, (len(ws), 1)).T
    WS, WD = np.meshgrid(ws, wd)
    sector_freq_2d = np.tile(sector_freq[:, np.newaxis], (1, len(ws)))
    
    # Crear dataset
    ds = xr.Dataset({
        'Weibull_A': (['wd', 'ws'], A_2d),
        'Weibull_k': (['wd', 'ws'], k_2d),
        'Sector_frequency': (['wd', 'ws'], sector_freq_2d),
        'WS': (['wd', 'ws'], WS),
        'WD': (['wd', 'ws'], WD),
        'TI': (['wd', 'ws'], np.full((len(wd), len(ws)), 0.08))
    })
    
    ds = ds.assign_coords(wd=wd, ws=ws)
    
    print("Dataset creado exitosamente!")
    print(f"Rango wd: {ds.wd.values[0]} - {ds.wd.values[-1]}°")
    print(f"Rango ws: {ds.ws.values[0]} - {ds.ws.values[-1]} m/s")
    
    return XRSite(ds)

def crear_turbinas_predefinidas():
    """Usar turbinas predefinidas de PyWake"""
    from py_wake.examples.data.hornsrev1 import V80
    print("Usando turbina V80 predefinida")
    return V80()

def analizar_perdidas_simple():
    """Análisis simplificado para evitar errores"""
    
    print("=== ANÁLISIS SIMPLIFICADO DE PÉRDIDAS ===\n")
    
    # 1. Crear sitio
    site = crear_site_offshore_con_weibull()
    
    # 2. Usar turbinas predefinidas
    turbinas = crear_turbinas_predefinidas()
    
    # 3. Configurar modelo de wake
    wake_model = BastankhahGaussian(site, turbinas)
    
    # 4. Diseño simple del parque
    x = np.array([0, 400, 800])
    y = np.array([0, 0, 0])
    
    print(f"Layout del parque: {len(x)} turbinas")
    
    # 5. Simulación con parámetros específicos
    print("\nEjecutando simulación...")
    
    # Usar solo algunas direcciones y velocidades clave
    wd_simulacion = [0, 90, 180, 270]
    ws_simulacion = [4, 8, 12, 16]
    
    resultados = wake_model(
        x, y,
        ws=ws_simulacion,
        wd=wd_simulacion,
        TI=0.08
    )
    
    # 6. Análisis de resultados
    print("\n=== RESULTADOS PRELIMINARES ===")
    
    # Calcular potencia total de forma robusta
    try:
        potencia_total = float(resultados.P.sum().values)
        print(f"Potencia total producida: {potencia_total:.0f} kW")
    except:
        potencia_total = 0
        print("No se pudo calcular la potencia total")
    
    # Calcular AEP si es posible
    try:
        aep = resultados.aep().sum()
        print(f"Producción anual estimada (AEP): {aep:.2f} GWh")
    except:
        print("No se pudo calcular el AEP")
    
    return resultados, site, wake_model, x, y

def visualizar_resultados_simple(resultados, site, x, y):
    """Visualización simplificada y robusta"""
    
    plt.figure(figsize=(12, 8))
    
    # 1. Layout del parque
    plt.subplot(2, 2, 1)
    plt.scatter(x, y, s=200, c='red', marker='o')
    for i, (xi, yi) in enumerate(zip(x, y)):
        plt.annotate(f'T{i+1}', (xi, yi), xytext=(10, 10), textcoords='offset points', fontsize=12)
    plt.title('Layout del Parque Eólico Offshore')
    plt.xlabel('X (m)')
    plt.ylabel('Y (m)')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    
    # 2. Potencia por turbina - VERSIÓN CORREGIDA
    plt.subplot(2, 2, 2)
    try:
        # Manejar diferentes tipos de resultados
        if hasattr(resultados, 'P') and resultados.P is not None:
            # Convertir a numpy array para manejar consistentemente
            if hasattr(resultados.P, 'values'):
                potencia_data = resultados.P.values
                if potencia_data.size > 0:
                    # Calcular potencia promedio por turbina
                    if len(potencia_data.shape) >= 3:  # [wt, wd, ws]
                        potencia_por_turbina = np.mean(potencia_data, axis=(1, 2))
                    elif len(potencia_data.shape) == 2:  # [wt, wd] o [wt, ws]
                        potencia_por_turbina = np.mean(potencia_data, axis=1)
                    else:  # [wt]
                        potencia_por_turbina = potencia_data
                    
                    # Asegurar que sea un array 1D
                    potencia_por_turbina = np.array(potencia_por_turbina).flatten()
                    
                    n_turbinas = len(potencia_por_turbina)
                    plt.bar(range(n_turbinas), potencia_por_turbina)
                    plt.title(f'Potencia Promedio por Turbina\n({n_turbinas} turbinas)')
                    plt.xlabel('Número de Turbina')
                    plt.ylabel('Potencia (kW)')
                    plt.grid(True, alpha=0.3)
                else:
                    plt.text(0.5, 0.5, 'No hay datos de potencia', 
                            ha='center', va='center', transform=plt.gca().transAxes)
            else:
                plt.text(0.5, 0.5, 'Formato de datos no reconocido', 
                        ha='center', va='center', transform=plt.gca().transAxes)
        else:
            plt.text(0.5, 0.5, 'No hay datos de potencia disponibles', 
                    ha='center', va='center', transform=plt.gca().transAxes)
    except Exception as e:
        plt.text(0.5, 0.5, f'Error al graficar potencia:\n{str(e)}', 
                ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Potencia por Turbina - Error')
    
    # 3. Distribución de direcciones
    plt.subplot(2, 2, 3)
    try:
        wd = site.ds.wd.values
        freq = site.ds.Sector_frequency.isel(ws=0).values
        plt.bar(wd, freq, width=8, alpha=0.7)
        plt.title('Distribución de Direcciones de Viento')
        plt.xlabel('Dirección (°)')
        plt.ylabel('Frecuencia')
        plt.grid(True, alpha=0.3)
    except Exception as e:
        plt.text(0.5, 0.5, f'Error en distribución direcciones:\n{str(e)}', 
                ha='center', va='center', transform=plt.gca().transAxes)
    
    # 4. Información del sistema
    plt.subplot(2, 2, 4)
    try:
        info_text = [
            f'Sitio Offshore',
            f'Velocidad media: {site.ds.Weibull_A.mean().values:.1f} m/s',
            f'Parámetro k: {site.ds.Weibull_k.mean().values:.1f}',
            f'Turbulencia: {site.ds.TI.mean().values:.3f}',
            f'Turbinas: {len(x)}',
            f'Separación: 400 m',
            f'Modelo: BastankhahGaussian'
        ]
        
        plt.text(0.1, 0.9, '\n'.join(info_text), fontsize=11, 
                 verticalalignment='top', transform=plt.gca().transAxes)
        plt.axis('off')
        plt.title('Configuración del Sistema')
    except Exception as e:
        plt.text(0.5, 0.5, f'Error en información:\n{str(e)}', 
                ha='center', va='center', transform=plt.gca().transAxes)
    
    plt.tight_layout()
    plt.show()

def analisis_turbulencia_especifico():
    """Análisis específico del efecto de la turbulencia"""
    
    print("\n=== ANÁLISIS DE TURBULENCIA ===")
    
    try:
        site = crear_site_offshore_con_weibull()
        turbinas = crear_turbinas_predefinidas()
        wake_model = BastankhahGaussian(site, turbinas)
        
        x = np.array([0, 400, 800])
        y = np.array([0, 0, 0])
        
        # Probar diferentes valores de TI
        ti_values = [0.06, 0.08, 0.10, 0.12]
        ws_test = 12
        wd_test = 270
        
        print(f"Analizando efecto de TI a {ws_test} m/s, {wd_test}°")
        print("TI\tPotencia Total (kW)")
        print("-" * 25)
        
        potencias = []
        for ti in ti_values:
            resultados = wake_model(x, y, ws=ws_test, wd=wd_test, TI=ti)
            try:
                potencia_total = float(resultados.P.sum().values)
                potencias.append(potencia_total)
                print(f"{ti}\t{potencia_total:.0f}")
            except:
                potencias.append(0)
                print(f"{ti}\tError en cálculo")
        
        # Gráfico de efecto de TI
        if len(potencias) > 0:
            plt.figure(figsize=(10, 6))
            plt.plot(ti_values, potencias, 'o-', linewidth=2, markersize=8)
            plt.title('Efecto de la Turbulencia en la Producción de Potencia')
            plt.xlabel('Intensidad de Turbulencia (TI)')
            plt.ylabel('Potencia Total (kW)')
            plt.grid(True, alpha=0.3)
            plt.show()
        else:
            print("No se pudieron calcular las potencias para el gráfico")
            
    except Exception as e:
        print(f"Error en análisis de turbulencia: {e}")

def mostrar_detalles_resultados(resultados):
    """Mostrar detalles de los resultados para debugging"""
    print("\n=== DETALLES DE RESULTADOS ===")
    
    if hasattr(resultados, 'P'):
        print(f"Tipo de resultados.P: {type(resultados.P)}")
        if hasattr(resultados.P, 'shape'):
            print(f"Forma de resultados.P: {resultados.P.shape}")
        if hasattr(resultados.P, 'dims'):
            print(f"Dimensiones de resultados.P: {resultados.P.dims}")
        if hasattr(resultados.P, 'values'):
            print(f"Tipo de valores: {type(resultados.P.values)}")
            if hasattr(resultados.P.values, 'shape'):
                print(f"Forma de valores: {resultados.P.values.shape}")
    
    # Intentar calcular métricas básicas
    try:
        if hasattr(resultados, 'aep'):
            aep = resultados.aep()
            print(f"AEP calculado: {aep}")
    except:
        print("No se pudo calcular AEP")

# EJECUTAR ANÁLISIS COMPLETO
if __name__ == "__main__":
    try:
        print("INICIANDO SIMULACIÓN OFFSHORE...")
        
        # Análisis principal
        resultados, site, wake_model, x, y = analizar_perdidas_simple()
        
        # Mostrar detalles para debugging
        mostrar_detalles_resultados(resultados)
        
        # Visualización
        visualizar_resultados_simple(resultados, site, x, y)
        
        # Análisis de turbulencia
        analisis_turbulencia_especifico()
        
        print(f"\n=== SIMULACIÓN COMPLETADA ===")
        
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()