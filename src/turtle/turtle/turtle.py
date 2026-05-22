"""No ROS 2 que desenha o contorno extraido da imagem no turtlesim.

A pipeline de visao (notebook) gera `pontos.json`: uma lista ordenada de
coordenadas (x, y) ja no espaco do turtlesim. Este no apenas carrega esses
pontos e usa os servicos do turtlesim para desenhar:

- /turtle1/set_pen          -> liga/desliga a caneta (e define cor/espessura)
- /turtle1/teleport_absolute-> move a tartaruga direto para uma posicao (x, y)

Desenhamos com teleport (em vez de cmd_vel) porque o caminho ja esta em ordem
e queremos um traco fiel ao contorno, sem o erro acumulado de um controlador
de velocidade.
"""

import json
import os

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

# No ROS 2 Humble os servicos do turtlesim ficam no pacote `turtlesim`.
from turtlesim.srv import SetPen, TeleportAbsolute


class TurtleController(Node):

    def __init__(self):
        super().__init__('turtle_controller')

        # 1. Carrega os pontos gerados pela pipeline (instalados junto do pacote)
        caminho = os.path.join(
            get_package_share_directory('turtle_draw'), 'pontos.json')
        with open(caminho, 'r') as arquivo:
            self.pontos = json.load(arquivo)['pontos']
        self.get_logger().info(f'{len(self.pontos)} pontos carregados de {caminho}')

        # 2. Cria os clientes dos servicos e espera o turtlesim estar no ar
        self.cliente_caneta = self.create_client(SetPen, '/turtle1/set_pen')
        self.cliente_teleport = self.create_client(
            TeleportAbsolute, '/turtle1/teleport_absolute')
        self.cliente_caneta.wait_for_service()
        self.cliente_teleport.wait_for_service()

        # 3. Desenha
        self.desenhar()

    def usar_caneta(self, ligada, r=0, g=0, b=0, largura=2):
        """Liga (off=0) ou desliga (off=1) a caneta da tartaruga."""
        req = SetPen.Request()
        req.r, req.g, req.b = r, g, b
        req.width = largura
        req.off = 0 if ligada else 1
        futuro = self.cliente_caneta.call_async(req)
        rclpy.spin_until_future_complete(self, futuro)

    def ir_para(self, x, y):
        """Teletransporta a tartaruga para a posicao (x, y)."""
        req = TeleportAbsolute.Request()
        req.x = float(x)
        req.y = float(y)
        req.theta = 0.0
        futuro = self.cliente_teleport.call_async(req)
        rclpy.spin_until_future_complete(self, futuro)

    def desenhar(self):
        if not self.pontos:
            self.get_logger().warn('Nenhum ponto para desenhar.')
            return

        # Vai ate o primeiro ponto com a caneta DESLIGADA (nao risca o caminho ate la)
        x0, y0 = self.pontos[0]
        self.usar_caneta(False)
        self.ir_para(x0, y0)

        # Liga a caneta e percorre o contorno em ordem
        self.usar_caneta(True)
        for i, (x, y) in enumerate(self.pontos):
            self.ir_para(x, y)
            if i % 25 == 0:
                self.get_logger().info(f'desenhando ponto {i}/{len(self.pontos)}')

        self.get_logger().info('Desenho concluido.')


def main(args=None):
    rclpy.init(args=args)
    no = TurtleController()
    no.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()