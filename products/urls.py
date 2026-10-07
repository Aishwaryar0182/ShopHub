from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path(
        "product/<int:product_id>/",
        views.product_detail,
        name="product_detail"
    ),

    path(
        "add-to-cart/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),

    path(
        "cart/",
        views.view_cart,
        name="view_cart"
    ),

    path(
        "update-cart/<int:product_id>/",
        views.update_cart,
        name="update_cart"
    ),

    path(
        "clear-cart/",
        views.clear_cart,
        name="clear_cart"
    ),

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "order-success/<int:order_id>/",
        views.order_success,
        name="order_success"
    ),

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "wishlist/",
        views.wishlist,
        name="wishlist"
    ),

    path(
        "wishlist/toggle/<int:product_id>/",
        views.toggle_wishlist,
        name="toggle_wishlist"
    ),

    path(
        "my-orders/",
        views.my_orders,
        name="my_orders"
    ),

    path(
        "my-orders/<int:order_id>/",
        views.order_detail,
        name="order_detail"
    ),
]