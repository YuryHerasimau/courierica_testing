class Endpoints:

    class AuthEndpoints:
        login_by_email = "/login/email"
        login_by_phone = "/login/phone/code"

    class CompanyEndpoints:
        list_of_companies = "/companies"
        create_company = "/company"

    class DeliveryEndpoints:
        list_of_deliveries = "/deliveries"
        create_delivery = "/delivery"
    
    class CourierEndpoints:
        list_of_couriers = "/couriers"
        create_courier = "/courier"

    class PickupPointEndpoints:
        list_of_pickup_points = "/pickup_points"
        create_pickup_point = "/pickup_point"

    class RouteEndpoints:
        list_of_routes = "/routes"
        create_route = "/route"