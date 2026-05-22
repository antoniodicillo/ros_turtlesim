import json
import os
import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

# Kilted Kaiju: turtlesim_msgs is now its own package (split from turtlesim).
# Install with: sudo apt install ros-kilted-turtlesim
from turtlesim_msgs.srv import SetPen, TeleportAbsolute


class TurtleController(Node):
    def __init__(self):
        super().__init__('turtle_controller')

        # 1. Carrega os points gerados pela pipeline
        try:
            caminho = os.path.join(
                get_package_share_directory('turtle'), 'points.json')
            with open(caminho, 'r') as arquivo:
                self.points = json.load(arquivo)['points']
            self.get_logger().info(
                f'{len(self.points)} points carregados de {caminho}')
        except Exception as e:
            self.get_logger().error(f'Erro ao carregar o arquivo JSON: {e}')
            self.points = []
            return

        # 2. Cria os clientes dos servicos
        self.cliente_caneta = self.create_client(SetPen, '/turtle1/set_pen')
        self.cliente_teleport = self.create_client(
            TeleportAbsolute, '/turtle1/teleport_absolute')

    def aguardar_servicos(self):
        """Espera os servicos estarem disponiveis de forma limpa."""
        while not self.cliente_caneta.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Aguardando servico /turtle1/set_pen...')
        while not self.cliente_teleport.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                'Aguardando servico /turtle1/teleport_absolute...')

    def usar_caneta(self, ligada, r=0, g=0, b=0, largura=2):
        """Liga ou desliga a caneta da tartaruga."""
        req = SetPen.Request()
        req.r, req.g, req.b = r, g, b
        req.width = largura
        req.off = 0 if ligada else 1

        futuro = self.cliente_caneta.call_async(req)
        rclpy.spin_until_future_complete(self, futuro)
        return futuro

    def ir_para(self, x, y):
        """Teletransporta a tartaruga para a posicao (x, y)."""
        req = TeleportAbsolute.Request()
        req.x = float(x)
        req.y = float(y)
        req.theta = 0.0

        futuro = self.cliente_teleport.call_async(req)
        rclpy.spin_until_future_complete(self, futuro)
        return futuro

    def desenhar(self):
        if not self.points:
            self.get_logger().warn('Nenhum ponto para desenhar.')
            return

        # BUG FIX: era `self.points` (lista inteira), deve ser `self.points[0]`
        x0, y0 = self.points[0]

        # Vai ate o primeiro ponto com a caneta DESLIGADA
        self.usar_caneta(False)
        self.ir_para(x0, y0)

        # Liga a caneta e percorre o contorno em ordem
        self.usar_caneta(True)

        for i, (x, y) in enumerate(self.points):
            self.ir_para(x, y)
            if i % 25 == 0:
                self.get_logger().info(
                    f'Desenhando ponto {i}/{len(self.points)}')

        self.get_logger().info('Desenho concluido.')


def main(args=None):
    rclpy.init(args=args)
    no = TurtleController()

    if no.points:
        # BUG FIX: aguardar_servicos() deve vir ANTES de desenhar()
        no.aguardar_servicos()
        no.desenhar()

    no.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
