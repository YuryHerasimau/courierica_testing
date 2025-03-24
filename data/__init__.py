from data.endpoints import Endpoints


def get_auth_endpoints():
    return Endpoints.AuthEndpoints()
    
def get_company_endpoints():
    return Endpoints.CompanyEndpoints()

def get_delivery_endpoints():
    return Endpoints.DeliveryEndpoints()

def get_courier_endpoints():
    return Endpoints.CourierEndpoints()

def get_pickup_point_endpoints():
    return Endpoints.PickupPointEndpoints()

def get_route_endpoints():
    return Endpoints.RouteEndpoints()