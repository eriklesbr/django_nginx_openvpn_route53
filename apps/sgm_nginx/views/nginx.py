import subprocess
import nginx
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sismais_gateway_manager.settings import env


class ConfigViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        """
        Recebe os campos e cria uma configuração no NginX de acordo com o modo de operação
        """

        obj = request.data
        file_name = ''
        port_dest = ''
        
        try:      
            # Verifica se os parâmetros subdominio e ip_vpn_cliente foram passados e cria um nome exclusivo para o arquivo NginX
            if {'subdominio', 'ip_vpn_cliente', 'id'} <= obj.keys():
                file_name = f'{obj["id"]}-{obj["subdominio"]}-{obj["ip_vpn_cliente"]}' if obj["subdominio"] and obj["ip_vpn_cliente"] and obj["id"] else None
            else:
                raise ValueError('Informe corretamente os campos ID, Subdomínio e IP VPN')

            # Verifica se as portas iniciais e finais de destino foram passados e cria um intervalo de porta
            if {'porta_destino_inicial', 'porta_destino_final'} <= obj.keys():
                port_dest = obj['porta_destino_inicial'] if obj['porta_destino_inicial'] == obj['porta_destino_final'] else '$server_port'
            elif {'porta_destino_inicial'} <= obj.keys():
                port_dest = obj['porta_destino_inicial']
            elif {'porta_destino_final'} <= obj.keys():
                port_dest = obj['porta_destino_final']
            else:
                port_dest = '$server_port'

            # Verifica se as portas iniciais e finais de destino foram passados e cria um intervalo de porta
            if {'porta_origem_inicial', 'porta_origem_final'} <= obj.keys():
                port_orin = obj['porta_origem_inicial'] if obj['porta_origem_inicial'] == obj['porta_origem_final'] else f'{obj["porta_origem_inicial"]}-{obj["porta_origem_final"]}'
            elif {'porta_origem_inicial'} <= obj.keys():
                port_orin = obj['porta_origem_inicial']
            elif {'porta_origem_final'} <= obj.keys():
                port_orin = obj['porta_origem_final']
            else:
                port_orin = '80'

            # Criando arquivo de configuração
            c = nginx.Conf()

            # criando modo proxy reverse
            if request.data['modo_nginx'] == '1':
                s = nginx.Server()
                s.add(
                    nginx.Key('listen', f'{port_orin}'),
                    nginx.Key('server_name', request.data["subdominio"]),
                    nginx.Location('/',
                        nginx.Key(
                            'proxy_pass',
                            f'http://{request.data["ip_vpn_cliente"]}:{port_dest}'
                        ),
                        nginx.Key('proxy_http_version', '1.1'),
                        nginx.Key('proxy_set_header', 'Upgrade $http_upgrade'),
                        nginx.Key('proxy_set_header', 'Connection "Upgrade"'),
                        nginx.Key('proxy_set_header', 'Host $host')
                    ),
                )
                c.add(s)

            # adicionando modo ao arquivo de configuração
            nginx.dumpf(c, f'/etc/nginx/sites-available/{file_name}')

            # Aplicando as configurações no NginX
            try:
                response = subprocess.run(
                    [
                        'sudo', '-S', 'ln', '-s',
                        f'/etc/nginx/sites-available/{file_name}',
                        f'/etc/nginx/sites-enabled/'
                    ],
                    capture_output=True,
                    text=True,
                    start_new_session=True,
                    input=f'{env("PASS_USER")}\n'
                )
                if response.returncode == 0:
                    try:
                        response2 = subprocess.run(
                            ['sudo', '-S', 'nginx', '-t'],
                            capture_output=True,
                            text=True,
                            start_new_session=True,
                            input=f'{env("PASS_USER")}\n'
                        )
                        if response2.returncode == 0:
                            try:
                                response3 = subprocess.run(
                                    ['sudo', '-S', 'systemctl', 'reload', 'nginx'],
                                    capture_output=True,
                                    text=True,
                                    start_new_session=True,
                                    input=f'{env("PASS_USER")}\n'
                                )
                                if response3.returncode == 0:
                                    return Response({
                                        "file": f'{file_name}',
                                        "config": c.as_dict
                                    }, status.HTTP_201_CREATED)
                            except Exception as e:
                                raise Exception(e.__str__())
                    except Exception as e:
                        raise Exception(e.__str__())
            except Exception as e:
                raise Exception(f"Erro ao criar link simbólico para: /etc/nginx/sites-enabled/{file_name}")
        except ValueError as v:
            return Response({"message": v.__str__()}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': e.__str__()}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request):
        try:
            return Response({}, status.HTTP_200_OK)
        except Exception as e:
            return Response({}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        try:
            return Response({}, status.HTTP_200_OK)
        except Exception as e:
            return Response({}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        """
        Recebe id para realizar a exclusão da configuração do NginX
        Obs: O ID informado na URI deve ter o caractere '.' alterado para '@'.
        Exemplo: 56-dev.sismais.net-192.168.0.1
                 56-dev@sismais@net-192@168@0@1
        Função em python: 
            str.replace('.', '@') para adiconar o @ ou
            str.replace('@', '.') para retornar o .
        """
        try:
            # Converte @ em ponto para realizar a exclusão do arquivo
            pk = pk.replace('@', '.')
            response = subprocess.run(
                ['sudo', '-S', 'rm', f'/etc/nginx/sites-available/{pk}', f'/etc/nginx/sites-enabled/{pk}'],
                capture_output=True, text=True, start_new_session=True, input=f'{env("PASS_USER")}\n'
            )
            if response.returncode == 0:
                response2 = subprocess.run(
                    ['sudo', '-S', 'nginx', '-t'],
                    capture_output=True, text=True, start_new_session=True, input=f'{env("PASS_USER")}\n'
                )
                if response2.returncode == 0:
                    response3 = subprocess.run(
                        ['sudo', '-S', 'systemctl', 'reload', 'nginx'],
                        capture_output=True, text=True, start_new_session=True, input=f'{env("PASS_USER")}\n'
                    )
                    if response3.returncode == 0:
                        return Response({}, status.HTTP_204_NO_CONTENT)
                    raise Exception(f"Erro ao recarregar configurações do NginX: {response3.stderr.__str__()}")
                raise Exception(f"Erro ao testar configurações do NginX: {response2.stderr.__str__()}")
            raise ValueError(f"Erro ao remover {pk}: {response.stderr.__str__()}")
        except ValueError as e:
            return Response({}, status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"message": e.__str__()}, status.HTTP_500_INTERNAL_SERVER_ERROR)
