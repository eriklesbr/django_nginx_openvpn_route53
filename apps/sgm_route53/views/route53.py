from rest_framework.permissions import IsAuthenticated
import route53
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models.route53 import Route53



class HostedZoneViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    """
    Classe responsável por gerenciar as Zonas Hospedadas
    """

    conn = Route53().conn
    
    def create(self, request):
        try:
            new_zone, change_info = self.conn.create_hosted_zone(
                name=request.data['name'], comment=request.data['comment']
            )
        except TypeError as e:
            return Response({
                "message": f"O domínio {request.data['name']} não está disponível."
            }, status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            return Response({
                "message": e.__str__()
            }, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            "id": new_zone.id,
            "name": new_zone.name,
            "info": change_info.__str__()
        }, status.HTTP_201_CREATED)

    def list(self, request):
        response = []
        try:
            for i, zone in enumerate(self.conn.list_hosted_zones()):
                response.append(
                    {
                        "id": zone.id,
                        "name": zone.name[:-1],
                        "caller_reference": zone.caller_reference,
                        "resource_record_set_count": zone.resource_record_set_count,
                        "comment": zone.comment
                    }
                )
                """record_sets = []
                for record_set in zone.record_sets:
                    record_sets.append(
                        {
                            "name": record_set.name[:-1],
                            "records": record_set.records,
                            "ttl": record_set.ttl,
                            "region": record_set.region,
                            "weight": record_set.weight,
                            "set_identifier": record_set.set_identifier
                        }
                    )
                response[i]['record_sets'] = record_sets"""
        except Exception as e:
            return Response(
                {
                    "message": e.__str__()
                }, status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(response, status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        response = {}
        try:
            zone = self.conn.get_hosted_zone_by_id(pk)
            record_sets = []
            for record_set in zone.record_sets:
                record_sets.append(
                    {
                        "name": record_set.name[:-1],
                        # "records": record_set.records,
                        # "ttl": record_set.ttl,
                        # "region": record_set.region,
                        # "weight": record_set.weight,
                        # "set_identifier": record_set.set_identifier
                    }
                )
            response = {
                "id": zone.id,
                "name": zone.name[:-1],
                "caller_reference": zone.caller_reference,
                "resource_record_set_count": zone.resource_record_set_count,
                "comment": zone.comment,
                "record_sets": record_sets
            }
        except Exception as e:
            return Response({'message': e.__str__()})
        return Response(response, status.HTTP_200_OK)   
    
    def destroy(self, request, pk=None):
        try:
            zone = self.conn.get_hosted_zone_by_id(pk)
            zone.delete(force=True)
        except Exception as e:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            message = e.__str__()
            if message.find('404') != -1:
                message = "O domínio não foi encontrado: " + message
                status_code = status.HTTP_404_NOT_FOUND
            return Response({
                'message': message
            }, status_code)
        return Response({}, status.HTTP_204_NO_CONTENT)


class RecordSetViewSet(viewsets.ViewSet):

    conn = route53.connect(
        aws_access_key_id='AKIATIRSJF2JPXQ7QHO4',
        aws_secret_access_key='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',
    )

    def create(self, request, hosted_zone_pk=None):
        try:
            zone = self.conn.get_hosted_zone_by_id(hosted_zone_pk)
            if request.data['tipo_apontamento_dns'] == '1':
                new_record, change_info = zone.create_a_record(
                    name=request.data['name'],
                    values=request.data['values'].split(','),
                    ttl=request.data['ttl']
                )
            elif request.data['tipo_apontamento_dns'] == '2':
                new_record, change_info = zone.create_cname_record(
                    name=request.data['name'],
                    values=request.data['values'].split(','),
                    ttl=request.data['ttl']
                )
        except Exception as e:
            message = e.__str__()
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if message.find('but it already exists') != -1:
                message = 'Erro: O nome do DNS informado já existe! ' + message
                status_code = status.HTTP_400_BAD_REQUEST
            elif message.find('is not permitted in zone') != -1:
                message = 'Erro: O nome do DNS informado não é permitido!: ' + message
                status_code = status.HTTP_400_BAD_REQUEST
            return Response({
                "message": message
            }, status_code)
            
        return Response({
            "name": new_record.name,
            "records": new_record.records,
            "ttl": new_record.ttl,
            "region": new_record.region,
            "weight": new_record.weight,
            "set_identifier": new_record.set_identifier
        }, status.HTTP_201_CREATED)

    def list(self, request, hosted_zone_pk=None):
        response = []
        try:
            zone = self.conn.get_hosted_zone_by_id(hosted_zone_pk)
            
            for record_set in zone.record_sets:
                response.append(
                    {
                        "name": record_set.name[:-1],
                        "records": record_set.records,
                        "ttl": record_set.ttl,
                        "region": record_set.region,
                        "weight": record_set.weight,
                        "set_identifier": record_set.set_identifier
                    }
                )
        except Exception as e:
            return Response({
                "message": e.__str__()
            }, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response, status.HTTP_200_OK)

    def retrieve(self, request, pk=None, hosted_zone_pk=None):
        response = {}
        try:
            status_code = status.HTTP_200_OK
            pk = pk.replace('@', '.') + '.'
            zone = self.conn.get_hosted_zone_by_id(hosted_zone_pk)
            for record_set in zone.record_sets:
                if record_set.name == pk:
                    record_set = record_set
                    break
                record_set = None
            if record_set:
                response = {
                    "name": record_set.name[:-1],
                    "records": record_set.records,
                    "ttl": record_set.ttl,
                    "region": record_set.region,
                    "weight": record_set.weight,
                    "set_identifier": record_set.set_identifier
                }
            else:
                status_code = status.HTTP_404_NOT_FOUND
        except Exception as e:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            message = e.__str__()
            return Response({
                "message": message
            }, status_code)
        return Response(response, status_code)
        
    def update(self, request, pk=None, hosted_zone_pk=None):
        try:
            response = {}
            status_code = status.HTTP_200_OK
            pk = pk.replace('@', '.') + '.'
            zone = self.conn.get_hosted_zone_by_id(hosted_zone_pk)
            for record_set in zone.record_sets:
                if record_set.name == pk:
                    record_set = record_set
                    break
                record_set = None
            if record_set:
                record_set.name = request.data['name']
                record_set.records = request.data['records'].split(',')
                record_set.ttl = request.data['ttl']
                record_set.save()
                response = {
                    "name": record_set.name,
                    "records": record_set.records,
                    "ttl": record_set.ttl,
                    "region": record_set.region,
                    "weight": record_set.weight,
                    "set_identifier": record_set.set_identifier
                }
            else:
                status_code = status.HTTP_404_NOT_FOUND
        except Exception as e:
            message = e.__str__()
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if message.find('Value is not a valid IPv4 address') != -1:
                message = 'Erro: O valor não é um IPv4 válido! ' + message
                status_code = status.HTTP_400_BAD_REQUEST
            return Response({
                "message": message
            }, status_code)
        return Response(response, status_code)
    
    def destroy(self, request, pk=None, hosted_zone_pk=None):
        try:
            pk = pk.replace('@', '.') + '.'
            zone = self.conn.get_hosted_zone_by_id(hosted_zone_pk)
            for record_set in zone.record_sets:
                if record_set.name == pk:
                    record_set = record_set
                    break
                record_set = None
            if record_set:
                record_set.delete()
        except Exception as e:
            message = e.__str__()
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({
                "message": message
            }, status_code)
        return Response({}, status.HTTP_204_NO_CONTENT)
