# Relatório Técnico — Turtle Draw

**Pipeline de Visão Computacional + Pacote ROS 2 (Kilted Kaiju)**  
*antonio · Ubuntu Linux · 2025*

---

## 1. Objetivo

Extrair o contorno da silhueta de `dog.jpg` (buldogue francês escuro sobre fundo claro) e fazer a tartaruga do `turtlesim` percorrê-lo. **Restrição:** OpenCV usado *apenas* para carregar a imagem; todo o processamento é feito com NumPy.

---

## 2. Pipeline de Visão Computacional

| # | Etapa | Decisão principal |
|---|-------|-------------------|
| 1 | **Recorte + Reamostragem** | ROI remove sombra do chão; decimação `FATOR=4` viabiliza loops Python |
| 2 | **Tons de Cinza** | Luminância BT.601: `L = 0.299R + 0.587G + 0.114B` |
| 3 | **Suavização Gaussiana** | Kernel manual com padding por replicação — preserva bordas reais |
| 4 | **Detecção Sobel** | Magnitude `√(gx²+gy²)`; marca todas as bordas, não gera caminho ordenado |
| 5 | **Segmentação Otsu** | Limiar automático + margem `t−15` para excluir sombra residual |
| 6 | **Morfologia + CC** | Fechamento/abertura → maior componente conexo (DFS-8) → kernel 9 costura peitoral/coleira |
| 7 | **Moore-Neighbor Tracing** | Percorre vizinhança-8 em sentido horário → sequência **ordenada e fechada** |
| 8 | **Simplificação + Mapeamento** | Subamostro `PASSO=3`; mapeia para turtlesim (0–11) com **eixo Y invertido** |

---

## 3. Pacote ROS 2

### Estrutura

```
ros_turtlesim/src/turtle/
├── turtle/
│   ├── __init__.py
│   └── turtle.py       # nó principal
├── resource/points.json
├── package.xml
└── setup.py
```

### Nó `turtle_controller`

Carrega `pontos.json` e usa dois serviços:

| Serviço | Tipo | Função |
|---------|------|--------|
| `/turtle1/set_pen` | `SetPen` | Liga/desliga caneta, define cor e largura |
| `/turtle1/teleport_absolute` | `TeleportAbsolute` | Move para (x, y, θ) sem passar pelos intermediários |

Rotina: move ao ponto inicial com caneta **desligada** → liga caneta → percorre todos os pontos em ordem.

**Teleport vs. cmd_vel:** o caminho já está ordenado e com coordenadas exatas; teleport elimina o erro acumulado de um controlador proporcional.

**Compatibilidade Kilted Kaiju:** serviços migrados para o pacote `turtlesim_msgs`:

```python
from turtlesim_msgs.srv import SetPen, TeleportAbsolute
# package.xml: <depend>turtlesim_msgs</depend>
```

---

## 4. Execução

```bash
source /opt/ros/kilted/setup.bash
cd ~/Desktop/ros_turtlesim && colcon build --packages-select turtle
source install/setup.bash
ros2 run turtlesim turtlesim_node   # terminal separado
ros2 run turtle turtle_draw
```

> Adicione `source /opt/ros/kilted/setup.bash` ao `~/.bashrc` para evitar repetição.

---

## 5. Conclusão

O Moore-Neighbor Tracing foi determinante para garantir um contorno fiel — pontos fora de ordem gerariam riscos cruzados. A separação pipeline/nó ROS 2 permite evoluir cada parte independentemente (ex.: detector mais sofisticado ou suporte a múltiplos contornos).
