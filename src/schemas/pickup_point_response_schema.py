from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Point(BaseModel):
    latitude: float
    longitude: float

class Firm(BaseModel):
    id: str
    name: str

class AutoAssignPriority(BaseModel):
    walking: int
    bike: int
    moto: int
    driving: int

class Settings(BaseModel):
    save_offline_delivered_date: bool
    hide_recipient_address_before_pickuped: bool
    route_strict_following: bool
    courier_require_order_confirmation: bool
    offline_enabled: bool

class Tracking(BaseModel):
    send_track_link: bool

class PickupPointCreateResponse(BaseModel):
    id: str
    company_id: str
    external_id: Optional[str]
    name: str
    address: str
    phone: Optional[str] = None
    point: Point
    zone: Optional[List[Point]] = Field(default_factory=list)
    currency: Optional[str] = "RUB"
    firm_id: Optional[str] = None
    created_at: datetime

class PickupPointItem(BaseModel):
    id: str
    external_id: Optional[str]
    name: str
    address: str
    phone: Optional[str]
    point: Point
    zone: Optional[List[Point]]
    auto_assign_enabled: bool
    auto_assign_queue_mode: bool
    auto_assign_queue_geo_disabled: bool
    auto_assign_version: str
    hide_recipient_address: bool
    time_pickup: int
    time_drop_off: int
    time_late: int
    time_cooking: int
    time_late_3pl: int
    time_arrive_3pl: int
    timezone: Optional[str]
    courier_id_3pl: Optional[str]
    courier_radius: int
    delivery_consolidation_radius: int
    default_max_deliveries_for_courier: int
    peak_time_max_deliveries_for_courier: int
    peak_load_hours: str
    default_time_to_assign_offset: int
    peak_time_to_assign_offset: int
    default_max_downtime_for_ready_delivery: int
    peak_time_max_downtime_for_ready_delivery: int
    skip_time_return_lock: bool
    courier_driving_average_speed: float
    courier_driving_unlimited_assign_radius: bool
    courier_driving_assign_radius_max: int
    courier_moto_average_speed: float
    courier_moto_unlimited_assign_radius: bool
    courier_moto_assign_radius_max: int
    courier_bike_average_speed: float
    courier_bike_unlimited_assign_radius: bool
    courier_bike_assign_radius_max: int
    courier_walking_average_speed: float
    courier_walking_unlimited_assign_radius: bool
    courier_walking_assign_radius_max: int
    auto_assign_priority_by_mood: AutoAssignPriority
    courier_delivered_mode: str
    courier_delivered_mode_distance: Optional[int]
    enabled: bool
    sub_alert_disabled: bool
    currency: Optional[str]
    firm: Optional[Firm]
    settings: Settings
    tracking: Tracking
    created_at: datetime
    updated_at: Optional[datetime]

class PickupPointByIdResponse(PickupPointItem):
    pass

class Pagination(BaseModel):
    page: int
    per_page: int
    total: int

class PickupPointsListSchema(BaseModel):
    pickup_points: List[PickupPointItem]
    pagination: Pagination