import subprocess
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from sismais_gateway_manager.settings import env
from rest_framework.permissions import IsAuthenticated


class VPNViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        id = request.data["id"]

        # Calcula automaticamente o IP com base no ID incrementando +1, afim de não utilizar o ip do servidor: 10.8.0.1
        ip = f"10.8.{int((int(id)+1)/256)}.{(int(id)+1)%256}"
        
        try:
            response = subprocess.run(
                ['ls', f'/home/{str(env.str("USER_NAME"))}/client-configs/files/client{id}.ovpn'],
                capture_output=True,
                text=True,
                start_new_session=True
            )
            if response.returncode == 0:
                return Response({
                    "name": f"client{id}",
                    "ip": ip,
                    "file": f"client{id}.ovpn",
                    "rota": f"v1/openvpn/{id}/download_file/"
                }, status.HTTP_208_ALREADY_REPORTED)
            try:
                subprocess.run(['rm', f'/home/{str(env.str("USER_NAME"))}/easy-rsa/pki/private/client{id}.key'])
                cmd2 = subprocess.run(
                    ['./easyrsa', 'gen-req', f'client{id}', 'nopass'],
                    capture_output=True,
                    start_new_session=True,
                    text=True,
                    cwd=f'/home/{str(env.str("USER_NAME"))}/easy-rsa',
                    input='\n'
                )
                if cmd2.returncode != 0:
                    raise Exception(f'Erro ao gerar requisitar certificado de autenticação: {cmd2.stdout}')
                try:
                    cmd3 = subprocess.run(
                        ['cp', f'/home/{str(env.str("USER_NAME"))}/easy-rsa/pki/private/client{id}.key', f'/home/{str(env.str("USER_NAME"))}/client-configs/keys/'],
                        capture_output=True, start_new_session=True, text=True
                    )
                    if cmd3.returncode != 0:
                        raise FileNotFoundError(f'Erro ao realizar a cópia da requisição do certificado de autenticação: {cmd3.stderr}')

                    try:
                        cmd4 = subprocess.run(
                            ['./easyrsa', 'sign-req', 'client', f'client{id}'],
                            capture_output=True,
                            start_new_session=True,
                            text=True,
                            cwd=f'/home/{str(env.str("USER_NAME"))}/easy-rsa',
                            input=f'yes\n{str(env.str("PASS_CA"))}\n'
                        )
                        if cmd4.returncode != 0:
                            raise Exception("Erro ao assinar o certificado de autenticação: ")
                        try:
                            cmd5 = subprocess.run(
                                ['cp', f'/home/{str(env.str("USER_NAME"))}/easy-rsa/pki/issued/client{id}.crt', f'/home/{str(env.str("USER_NAME"))}/client-configs/keys/'],
                                capture_output=True, start_new_session=True, text=True
                            )
                            if cmd5.returncode != 0:
                                raise Exception("Erro ao realizar a copia do certificado de autenticação: ")
                            try:
                                cmd6 = subprocess.run(
                                    ['sudo', '-S', 'cp', f'/home/{str(env.str("USER_NAME"))}/easy-rsa/ta.key', '/etc/openvpn/server/ca.crt', f'/home/{str(env.str("USER_NAME"))}/client-configs/keys/'],
                                    capture_output=True, start_new_session=True, text=True, input=f'{str(env.str("PASS_USER"))}\n'
                                )
                                if cmd6.returncode != 0:
                                    raise Exception("Erro ao atualizar o certificado de autenticação do servidor: ")
                                try:
                                    cmd7 = subprocess.run(
                                        ['./make_config.sh', f'client{id}'],
                                        capture_output=True, start_new_session=True, text=True,
                                        cwd=f'/home/{str(env.str("USER_NAME"))}/client-configs/'
                                    )
                                    if cmd7.returncode != 0:
                                        raise Exception(f"Erro ao gerar o arquivo de configuração: client{id}.ovpn")
                                    
                                    try:
                                        with open(f"/etc/openvpn/ccd/client{id}", 'w') as outfile:
                                            outfile.write(f"ifconfig-push {ip} 255.255.252.0")
                                        return Response(
                                        {
                                            "name": f"client{id}",
                                            "ip": ip,
                                            "file": f"client{id}.ovpn",
                                            "rota": f"v1/openvpn/{id}/download_file/"
                                        }, status.HTTP_201_CREATED
                                    )
                                    except Exception as e:
                                        return Response(
                                            {
                                                'message': e.__str__()
                                            }, status.HTTP_500_INTERNAL_SERVER_ERROR
                                        )
                                except Exception as e:
                                    raise Exception(e)
                            except Exception as e:
                                raise Exception(e)
                            
                        except Exception as e:
                            raise Exception(e)
                    except Exception as e:
                        raise Exception(e)
                    
                except Exception as e:
                    raise Exception(e)
                

            except FileNotFoundError as e:
                return Response(
                    {
                        'message': e.__str__()
                    }, status.HTTP_204_NO_CONTENT
                )
            except Exception as e:
                raise Exception("Erro ao solicitar a requisição a VPN: " + e.__str__())
            
        except Exception as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def list(self, request):
        try:
            response = subprocess.run(['ls', f'/home/{str(env.str("USER_NAME"))}/client-configs/files/'], capture_output=True, text=True)
            if response.returncode != 0:
                raise Exception(response.stderr)
            data = response.stdout.split()
            return Response({'data': data, "count": len(data)}, status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def retrieve(self, request, pk=None):

        try:
            response = subprocess.run(['cat', f'/etc/openvpn/ccd/client{pk}'], capture_output=True, text=True)
            if response.returncode != 0:
                raise Exception(response.stderr)
            data = response.stdout.split()
            data = {
                "ip": data[1],
                "sub-mask": data[2]
            }
            return Response(data, status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def destroy(self, request, pk=None):
        try:
            cmd1 = subprocess.run(
                ['./easyrsa', 'revoke', f'client{pk}'],
                capture_output=True, text=True, start_new_session=True, cwd=f'/home/{str(env.str("USER_NAME"))}/easy-rsa', input=f'yes\n{str(env.str("PASS_CA"))}\n'
            )
            if cmd1.returncode != 0:
                raise Exception(f'Erro ao tentar revogar o certificado client{pk}: {cmd1.stderr}')
            subprocess.run(
                [
                    'rm', f'/home/{str(env.str("USER_NAME"))}/client-configs/files/client{pk}.ovpn'
                ],
                capture_output=True, text=True, start_new_session=True
            )
            try:
                cmd2 = subprocess.run(
                    ['./easyrsa', 'gen-crl'],
                    capture_output=True, text=True, start_new_session=True, cwd=f'/home/{str(env.str("USER_NAME"))}/easy-rsa', input=f'{str(env.str("PASS_CA"))}\n'
                )
                if cmd2.returncode != 0:
                    raise Exception("Erro ao criar/atualizar CRL", cmd2.stderr.__str__())
                try:
                    cmd3 = subprocess.run(
                        ['sudo', '-S', 'cp', f'/home/{str(env.str("USER_NAME"))}/easy-rsa/pki/crl.pem', '/etc/openvpn/server/'],
                        capture_output=True, text=True, start_new_session=True, input=f'{str(env.str("PASS_USER"))}\n'
                    )
                    if cmd3.returncode != 0:
                        raise Exception("Erro ao atualizar CRL", cmd3.stderr.__str__())
                    subprocess.run(['sudo', '-S', 'rm', f'/etc/openvpn/ccd/client{pk}'],
                        capture_output=True, text=True, start_new_session=True, input=f'{str(env.str("PASS_USER"))}\n'
                    )
                    return Response(
                        {
                            "message": f'Certificado revogado com sucesso: {cmd3.stdout.__str__()}'
                        }, status.HTTP_204_NO_CONTENT
                    )
                except Exception as e:
                    raise Exception(e)

            except Exception as e:
                raise Exception(e)

        except Exception as e:
            return Response(
                {
                    "message": e.__str__()
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download_file(self, request, pk=None):
        try:
            file = open(f'/home/{str(env.str("USER_NAME"))}/client-configs/files/client{pk}.ovpn', 'rb')
            return FileResponse(file, as_attachment=True, filename=f'client{pk}.ovpn')
        except FileNotFoundError as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def restart_openvpn(self, request):
        try:
            cmd1 = subprocess.run(['sudo', '-S', 'systemctl', 'restart', 'openvpn-server@server.service'], capture_output=True, text=True, start_new_session=True, input=f'{str(env.str("PASS_USER"))}\n')
            if cmd1.returncode != 0:
                raise OSError(cmd1.stdout)
            return Response(
                {
                    "message": "O Serviço do OpenVPN foi reiniciado com sucesso!"
                }, status.HTTP_200_OK
            )
        except OSError as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def status_openvpn(self, request):
        try:
            cmd1 = subprocess.run(['sudo', '-S', 'systemctl', 'status', 'openvpn'], capture_output=True, text=True, input=f'{str(env.str("PASS_USER"))}\n')
            if cmd1.returncode != 0:
                raise OSError(cmd1.stdout)
            return Response(
                {
                    "message": cmd1.stdout.__str__().split('\n')
                }, status.HTTP_200_OK
            )
        except OSError as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def ping(self, request, pk=None):
        try:
            response = subprocess.run(['cat', f'/etc/openvpn/ccd/client{pk}'], capture_output=True, text=True)
            if response.returncode != 0:
                raise Exception(f"Erro ao buscar IP do cliente: {response.stderr.__str__()}")
            data = response.stdout.split()
            ip = data[1]

            response = subprocess.run(
                [
                    'ping', '-c', '10', ip
                ], capture_output=True, start_new_session=True
            )

            if response.returncode == 0:
                return Response(
                {
                    "message": response.stdout.decode('utf-8')
                }, status.HTTP_200_OK
            )
            raise Exception(f"Erro ao realizar o ping: {response.stdout.decode('utf-8')}")        
        except Exception as e:
            return Response(
                {
                    'message': e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
