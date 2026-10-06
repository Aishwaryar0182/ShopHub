from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import Product, Order, OrderItem, Wishlist


def get_cart_data(request):
    cart = request.session.get("cart", {})

    cart_items = []
    total = Decimal("0.00")

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id).first()

        if product is None:
            continue

        quantity = int(quantity)
        subtotal = product.price * quantity

        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return cart_items, total


def home(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    products = Product.objects.all().order_by("-created_at")

    if query:
        products = products.filter(name__icontains=query)

    if category:
        products = products.filter(category=category)

    categories = Product.objects.values_list(
        "category",
        flat=True
    ).distinct()

    cart = request.session.get("cart", {})
    cart_count = sum(cart.values())

    wishlist_ids = []

    if request.user.is_authenticated:
        wishlist_ids = list(
            Wishlist.objects.filter(
                user=request.user
            ).values_list("product_id", flat=True)
        )

    return render(request, "products/home.html", {
        "products": products,
        "query": query,
        "category": category,
        "categories": categories,
        "cart_count": cart_count,
        "wishlist_ids": wishlist_ids,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})

    wishlist_ids = []

    if request.user.is_authenticated:
        wishlist_ids = list(
            Wishlist.objects.filter(
                user=request.user
            ).values_list("product_id", flat=True)
        )

    return render(request, "products/product_detail.html", {
        "product": product,
        "cart_count": sum(cart.values()),
        "wishlist_ids": wishlist_ids,
    })


def add_to_cart(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)

        cart = request.session.get("cart", {})

        key = str(product.id)

        current_quantity = cart.get(key, 0)

        if current_quantity < product.stock:
            cart[key] = current_quantity + 1

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("view_cart")


def view_cart(request):
    cart_items, total = get_cart_data(request)

    cart = request.session.get("cart", {})

    return render(request, "products/cart.html", {
        "cart_items": cart_items,
        "total": total,
        "cart_count": sum(cart.values()),
    })


def update_cart(request, product_id):
    if request.method == "POST":
        cart = request.session.get("cart", {})

        key = str(product_id)

        action = request.POST.get("action")

        if key in cart:
            product = Product.objects.filter(
                id=product_id
            ).first()

            if action == "increase" and product:

                if cart[key] < product.stock:
                    cart[key] += 1

            elif action == "decrease":

                if cart[key] > 1:
                    cart[key] -= 1
                else:
                    del cart[key]

            elif action == "remove":
                del cart[key]

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("view_cart")


def clear_cart(request):
    if request.method == "POST":
        request.session["cart"] = {}
        request.session.modified = True

    return redirect("view_cart")


@login_required
def checkout(request):
    cart_items, total = get_cart_data(request)

    if not cart_items:
        return redirect("view_cart")

    error = ""

    if request.method == "POST":

        customer_name = request.POST.get(
            "customer_name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        if not customer_name or not phone or not address:

            error = "Please fill in all the fields."

        elif not phone.isdigit() or not 7 <= len(phone) <= 15:

            error = "Enter a valid phone number."

        else:

            for item in cart_items:

                if item["quantity"] > item["product"].stock:

                    error = (
                        f"Not enough stock for "
                        f"{item['product'].name}. "
                        f"Please update your cart."
                    )

                    break

            if not error:

                with transaction.atomic():

                    order = Order.objects.create(
                        user=request.user,
                        customer_name=customer_name,
                        phone=phone,
                        address=address,
                        total_amount=total,
                    )

                    for item in cart_items:

                        product = Product.objects.get(
                            id=item["product"].id
                        )

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            price=product.price,
                            quantity=item["quantity"],
                        )

                        product.stock -= item["quantity"]

                        product.save(
                            update_fields=["stock"]
                        )

                    request.session["cart"] = {}
                    request.session.modified = True

                return redirect(
                    "order_success",
                    order_id=order.id
                )

    return render(request, "products/checkout.html", {
        "cart_items": cart_items,
        "total": total,
        "error": error,
    })


@login_required
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "products/order_success.html",
        {
            "order": order
        }
    )


@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    cart = request.session.get("cart", {})
    cart_count = sum(cart.values())

    return render(
        request,
        "products/my_orders.html",
        {
            "orders": orders,
            "cart_count": cart_count,
        }
    )

@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "products/order_detail.html",
        {
            "order": order
        }
    )


def register(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not username or not password or not confirm_password:

            return render(
                request,
                "products/register.html",
                {
                    "error": "Please fill in all fields."
                }
            )

        if password != confirm_password:

            return render(
                request,
                "products/register.html",
                {
                    "error": "Passwords do not match."
                }
            )

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "products/register.html",
                {
                    "error": "Username already exists."
                }
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect("home")

    return render(
        request,
        "products/register.html"
    )


def login_view(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("home")

        return render(
            request,
            "products/login.html",
            {
                "error": "Invalid username or password."
            }
        )

    return render(
        request,
        "products/login.html"
    )


def logout_view(request):

    logout(request)

    return redirect("home")


@login_required
def toggle_wishlist(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()

    if wishlist_item:

        wishlist_item.delete()

    else:

        Wishlist.objects.create(
            user=request.user,
            product=product
        )

    return redirect("home")


@login_required
def wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related("product")

    return render(
        request,
        "products/wishlist.html",
        {
            "wishlist_items": wishlist_items
        }
    )