from django.db.models import Count
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

from .models import Channel, Server
from .schema import server_list_docs
from .serializer import ServerSerializer


class ServerListViewSet(viewsets.ViewSet):
    queryset = Server.objects.all()

    @server_list_docs
    def list(self, request):
        """Returns a list of servers filtered by various parameters.

        Thus method retrieves a queryset of servers based on the query parameters
        provided in the `request` object. The following query parameters are supported:

        - `category`: Filters servers by category name.
        - `qty`: Limits the number of servers returned.
        - `by_user`: Filters servers by user ID, only returning servers that the user is a member of.
        - `by_serverid`: Filters servers by server ID.
        - `with_num_members`: Annotates each server with the number of members it has.

        Args:
        request: A Django Request object containing query parameters

        Returns:
        A queryset of servers filtered by the specified parameters.

        Raises:
        - AuthenticationFailed:
            If the quer includes the 'by_user' or 'by_serverid' parameters and the user is not authenticated.
        - ValidationError:
            If there is an error parsing or validating the query parameters.
            This can occur if the `by_serverid` parameter is not a valid integer,
            or if server with the specified ID does not exist.

        Examples:
            To retrieve all servers in the 'gaming' category with at least 5 members,
            you can make the following reequest:

            GET /servers/?category=gaming&with_num_members=true&num_numbers__get=5

            To retrieve the first 10 servers that the authenticated user is a member of,
            you can make the following request:

            GET /servers/?by_user=true&qty=10
        """
        category = self.query_params.get("category")
        qty = self.query_params.get("qty")
        by_user = self.query_params.get("by_user") == "true"
        by_serverid = self.query_params.get("by_serverid")
        with_num_members = self.query_params.get("with_num_members") == "true"

        if category:
            self.queryset = self.queryset.filter(category__name=category)

        if by_user:
            if by_user and request.user.is_authenticated:
                user_id = request.user.id
                self.queryset = self.queryset.filter(member=user_id)
            else:
                raise AuthenticationFailed()

        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        if qty:
            self.queryset = self.queryset[: int(qty)]

        if by_serverid:
            if not request.user.is_authenticated:
                raise AuthenticationFailed()

            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server with id {by_serverid} not found")
            except ValueError:
                raise ValidationError(detail="Server value error")

        serializer = ServerSerializer(self.queryset, many=True, context={"num_members": with_num_members})
        return Response(serializer.data)
