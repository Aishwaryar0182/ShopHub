from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Product, Order, OrderItem, Wishlist


def get_cart_count(request):
    cart = request.session.get("cart", {})
    return sum(cart.values())


def home(request):
    products = Product.objects.all()

    query = request.GET.get("q")
    category = request.GET.get("category")

    if query:
        products = products.filter(name__icontains=query)

    if category and category != "All":
        products = products.filter(category=category)

    categories = Product.objects.values_list(
        "category",
        flat=True
    ).distinct()

    return render(
        request,
        "products/home.html",
        {
            "products": products,
            "categories": categories,
            "cart_count": get_cart_count(request),
        }
    )


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
            "cart_count": get_cart_count(request),
        }
    )


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    product_id = str(product_id)

    if product_id in cart:
        if cart[product_id] < product.stock:
            cart[product_id] += 1
    else:
        if product.stock > 0:
            cart[product_id] = 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("view_cart")


def view_cart(request):
    cart = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id).first()

        if product:
            item_total = product.price * quantity
            total += item_total

            cart_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "item_total": item_total,
                }
            )

    return render(
        request,
        "products/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
            "cart_count": get_cart_count(request),
        }
    )


def update_cart(request, product_id):
    cart = request.session.get("cart", {})
    product = get_object_or_404(Product, id=product_id)

    action = request.POST.get("action")
    product_id = str(product_id)

    if product_id not in cart:
        cart[product_id] = 1

    if action == "increase":
        if cart[product_id] < product.stock:
            cart[product_id] += 1

    elif action == "decrease":
        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    elif action == "remove":
        cart.pop(product_id, None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("view_cart")


def clear_cart(request):
    request.session["cart"] = {}
    request.session.modified = True

    return redirect("view_cart")


@login_required
def checkout(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("view_cart")

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id).first()

        if product:
            item_total = product.price * quantity
            total += item_total

            cart_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "item_total": item_total,
                }
            )

    if request.method == "POST":
        customer_name = request.POST.get("customer_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        if not customer_name or not phone or not address:
            messages.error(
                request,
                "Please fill all the details."
            )

            return render(
                request,
                "products/checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                    "cart_count": get_cart_count(request),
                }
            )

        for item in cart_items:
            if item["quantity"] > item["product"].stock:
                messages.error(
                    request,
                    f"Not enough stock for {item['product'].name}."
                )
                return redirect("view_cart")

        order = Order.objects.create(
            user=request.user,
            customer_name=customer_name,
            phone=phone,
            address=address,
            total_amount=total,
        )

        for item in cart_items:
            product = item["product"]
            quantity = item["quantity"]

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                price=product.price,
                quantity=quantity,
            )

            product.stock -= quantity
            product.save()

        request.session["cart"] = {}
        request.session.modified = True

        return redirect(
            "order_success",
            order_id=order.id
        )

    return render(
        request,
        "products/checkout.html",
        {
            "cart_items": cart_items,
            "total": total,
            "cart_count": get_cart_count(request),
        }
    )


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
            "order": order,
        }
    )


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username:
            messages.error(
                request,
                "Please enter a username."
            )
            return redirect("register")

        if not password:
            messages.error(
                request,
                "Please enter a password."
            )
            return redirect("register")

        if password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "Username already exists. Please choose another username."
            )
            return redirect("register")

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(
            request,
            "Registration successful. Please login."
        )

        return redirect("login")

    return render(
        request,
        "products/register.html"
    )


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(
            request,
            "Invalid username or password."
        )

        return redirect("login")

    return render(
        request,
        "products/login.html"
    )


def logout_view(request):
    logout(request)

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
            "wishlist_items": wishlist_items,
            "cart_count": get_cart_count(request),
        }
    )


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

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "home"
        )
    )


@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "products/my_orders.html",
        {
            "orders": orders,
            "cart_count": get_cart_count(request),
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
            "order": order,
            "cart_count": get_cart_count(request),
        }
    )