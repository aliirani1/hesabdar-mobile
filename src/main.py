import flet as ft
import json
import os
import hashlib
from datetime import datetime, timedelta

# ==================== تنظیمات ====================
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "accounting_data.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
INVOICE_DIR = os.path.join(DATA_DIR, "invoices")

COLORS = {
    "bg_dark": "#0f0f18",
    "bg_panel": "#1a1a2e",
    "bg_card": "#22223a",
    "bg_hover": "#2a2a45",
    "accent": "#00d2ff",
    "accent_hover": "#00b4d8",
    "success": "#4ecdc4",
    "danger": "#ff6b6b",
    "warning": "#ffaa00",
    "text": "#e0e0e0",
    "text_dim": "#8888a0",
    "border": "#333355",
}

# ==================== مدیریت داده ====================
class DataManager:
    def __init__(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            os.makedirs(INVOICE_DIR, exist_ok=True)
        except:
            pass
        
        self.data = {"products": [], "transactions": []}
        self.settings = {
            "username": "ali",
            "password": hashlib.sha256("1234".encode()).hexdigest()
        }
        self.load()

    def load(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            if "products" not in self.data:
                self.data["products"] = []
            if "transactions" not in self.data:
                self.data["transactions"] = []
        except Exception as e:
            print(f"خطا: {e}")
        
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
        except Exception as e:
            print(f"خطا: {e}")

    def save(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطا: {e}")
    
    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطا: {e}")

    def check_login(self, username, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return (username == self.settings["username"] and 
                hashed == self.settings["password"])

    def change_credentials(self, new_username, new_password):
        self.settings["username"] = new_username
        self.settings["password"] = hashlib.sha256(new_password.encode()).hexdigest()
        self.save_settings()

    def add_product(self, name, category, quantity):
        product = {
            "id": len(self.data["products"]) + 1,
            "name": name,
            "category": category,
            "quantity": int(quantity),
            "created_at": datetime.now().isoformat()
        }
        self.data["products"].append(product)
        self.save()
        return product

    def update_product(self, product_id, **kwargs):
        for p in self.data["products"]:
            if p["id"] == product_id:
                p.update(kwargs)
                self.save()
                return p
        return None

    def delete_product(self, product_id):
        self.data["products"] = [p for p in self.data["products"] if p["id"] != product_id]
        self.save()

    def get_product(self, product_id):
        for p in self.data["products"]:
            if p["id"] == product_id:
                return p
        return None

    def add_transaction(self, items, type_="sell"):
        total_qty = sum(item["quantity"] for item in items)
        transaction = {
            "id": len(self.data["transactions"]) + 1,
            "items": items,
            "total_quantity": total_qty,
            "type": type_,
            "date": datetime.now().isoformat()
        }
        self.data["transactions"].append(transaction)
        
        if type_ == "sell":
            for item in items:
                product = self.get_product(item["product_id"])
                if product:
                    product["quantity"] -= item["quantity"]
        
        self.save()
        return transaction

    def add_buy_transaction(self, product_id, quantity):
        product = self.get_product(product_id)
        if not product:
            return None
        
        transaction = {
            "id": len(self.data["transactions"]) + 1,
            "items": [{"product_id": product_id, "product_name": product["name"], 
                      "quantity": quantity}],
            "total_quantity": quantity,
            "type": "buy",
            "date": datetime.now().isoformat()
        }
        self.data["transactions"].append(transaction)
        product["quantity"] += int(quantity)
        self.save()
        return transaction

    def get_total_sold_quantity(self):
        return sum(t.get("total_quantity", 0) for t in self.data["transactions"] if t["type"] == "sell")

    def get_total_bought_quantity(self):
        return sum(t.get("total_quantity", 0) for t in self.data["transactions"] if t["type"] == "buy")

    def get_total_inventory(self):
        return sum(p["quantity"] for p in self.data["products"])

    def get_low_stock_products(self, threshold=3):
        return [p for p in self.data["products"] if p["quantity"] <= threshold]

    def reset_all(self):
        self.data = {"products": [], "transactions": []}
        self.save()


# ==================== برنامه اصلی ====================
def main(page: ft.Page):
    page.title = "تعمیرگاه موتور - سیستم مدیریت"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLORS["bg_dark"]
    page.padding = 0
    page.window.width = 400
    page.window.height = 800
    
    # راست‌چین کردن کل صفحه
    page.rtl = True
    
    dm = DataManager()
    current_user = {"logged_in": False}
    cart = {"items": []}
    
    # ==================== توابع کمکی ====================
    def show_message(text, color=COLORS["accent"]):
        snack = ft.SnackBar(
            content=ft.Text(text, color="#fff", font_family="Vazirmatn"),
            bgcolor=color,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    
    def create_field(label, hint="", password=False, value=""):
        return ft.TextField(
            label=label,
            hint_text=hint,
            password=password,
            value=value,
            bgcolor=COLORS["bg_card"],
            border_color=COLORS["border"],
            color=COLORS["text"],
            label_style=ft.TextStyle(color=COLORS["text_dim"]),
            border_radius=10,
            text_size=14,
            content_padding=15,
        )
    
    # ==================== صفحه لاگین ====================
    def show_login():
        username_field = create_field("نام کاربری", "ali")
        password_field = create_field("رمز عبور", "1234", password=True)
        
        def do_login(e):
            u = username_field.value.strip()
            p = password_field.value.strip()
            if dm.check_login(u, p):
                current_user["logged_in"] = True
                page.views.clear()
                show_main()
            else:
                show_message("❌ نام کاربری یا رمز عبور اشتباه است", COLORS["danger"])
        
        login_view = ft.View(
            route="/login",
            bgcolor=COLORS["bg_dark"],
            controls=[
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        controls=[
                            ft.Container(height=50),
                            ft.Text("🏍️", size=80, text_align=ft.TextAlign.CENTER),
                            ft.Text(
                                "تعمیرگاه موتور و لوازم یدکی",
                                size=20, weight=ft.FontWeight.BOLD,
                                color=COLORS["accent"], text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                "سیستم مدیریت انبار",
                                size=13, color=COLORS["text_dim"], text_align=ft.TextAlign.CENTER
                            ),
                            ft.Container(height=30),
                            ft.Container(
                                bgcolor=COLORS["bg_card"],
                                border_radius=20,
                                padding=25,
                                content=ft.Column(
                                    controls=[
                                        username_field,
                                        ft.Container(height=10),
                                        password_field,
                                        ft.Container(height=20),
                                        ft.ElevatedButton(
                                            "🔓 ورود به سیستم",
                                            on_click=do_login,
                                            bgcolor=COLORS["accent"],
                                            color="#fff",
                                            width=300,
                                            height=50,
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=10),
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                "نام کاربری: ali | رمز: 1234",
                                size=11, color=COLORS["text_dim"], text_align=ft.TextAlign.CENTER
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
        )
        page.views.append(login_view)
        page.update()
    
    # ==================== صفحه اصلی ====================
    def show_main():
        # ===== محتوای صفحات =====
        content_area = ft.Container(expand=True, padding=15)
        
        def build_dashboard():
            return ft.Column([
                ft.Text("📊 داشبورد", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=15),
                ft.Row([
                    stat_card("📤", "فروش", str(dm.get_total_sold_quantity()), COLORS["accent"]),
                    stat_card("📥", "خرید", str(dm.get_total_bought_quantity()), COLORS["success"]),
                ], spacing=10),
                ft.Container(height=10),
                ft.Row([
                    stat_card("🏪", "موجودی", str(dm.get_total_inventory()), COLORS["warning"]),
                    stat_card("📦", "کالاها", str(len(dm.data["products"])), COLORS["text"]),
                ], spacing=10),
                ft.Container(height=20),
                ft.Text("⚠️ هشدار موجودی کم", size=16, weight=ft.FontWeight.BOLD, color=COLORS["warning"]),
                ft.Container(height=10),
                ft.Column([low_stock_card(p) for p in dm.get_low_stock_products(3)] or 
                         [ft.Text("✅ همه کالاها موجودی کافی دارند", color=COLORS["success"], size=13)]),
            ], scroll=ft.ScrollMode.AUTO)
        
        def build_products():
            products_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            
            def refresh_products():
                products_list.controls.clear()
                for p in reversed(dm.data["products"]):
                    products_list.controls.append(product_card(p))
                if not dm.data["products"]:
                    products_list.controls.append(
                        ft.Text("📭 هیچ کالایی یافت نشد", color=COLORS["text_dim"], size=14)
                    )
                page.update()
            
            def open_add_dialog(e):
                name_field = create_field("نام کالا", "مثال: لاستیک")
                cat_field = create_field("دسته‌بندی", "مثال: لاستیک")
                qty_field = create_field("تعداد", "0")
                
                def save(e):
                    try:
                        n = name_field.value.strip()
                        c = cat_field.value.strip()
                        q = int(qty_field.value or 0)
                        if not n:
                            show_message("❌ نام کالا الزامی است", COLORS["danger"])
                            return
                        dm.add_product(n, c, q)
                        dialog.open = False
                        page.update()
                        refresh_products()
                        show_message("✅ کالا اضافه شد", COLORS["success"])
                    except:
                        show_message("❌ خطا در مقادیر", COLORS["danger"])
                
                dialog = ft.AlertDialog(
                    title=ft.Text("➕ افزودن کالا", color=COLORS["accent"]),
                    content=ft.Column([name_field, cat_field, qty_field], tight=True, spacing=10),
                    actions=[
                        ft.TextButton("ذخیره", on_click=save),
                        ft.TextButton("انصراف", on_click=lambda e: close_dialog(dialog)),
                    ],
                )
                page.overlay.append(dialog)
                dialog.open = True
                page.update()
            
            refresh_products()
            
            return ft.Column([
                ft.Row([
                    ft.Text("📦 مدیریت کالاها", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=COLORS["accent"], 
                                 icon_size=32, on_click=open_add_dialog),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                products_list,
            ], expand=True)
        
        def build_buy():
            if not dm.data["products"]:
                return ft.Column([
                    ft.Text("📥 ورود کالا", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ft.Container(height=30),
                    ft.Text("❌ ابتدا کالا اضافه کنید", color=COLORS["danger"], size=14),
                ])
            
            product_names = [f"{p['name']} (موجودی: {p['quantity']})" for p in dm.data["products"]]
            dropdown = ft.Dropdown(
                options=[ft.dropdown.Option(n) for n in product_names],
                value=product_names[0] if product_names else None,
                bgcolor=COLORS["bg_card"],
                border_color=COLORS["border"],
                color=COLORS["text"],
                border_radius=10,
                label="انتخاب کالا",
            )
            qty_field = create_field("تعداد ورودی", "10")
            
            def do_buy(e):
                try:
                    pname = dropdown.value.split(" (")[0]
                    product = next((p for p in dm.data["products"] if p["name"] == pname), None)
                    q = int(qty_field.value or 0)
                    if not product or q <= 0:
                        show_message("❌ مقادیر نامعتبر", COLORS["danger"])
                        return
                    dm.add_buy_transaction(product["id"], q)
                    show_message(f"✅ {q} عدد اضافه شد", COLORS["success"])
                    page.views.clear()
                    show_main()
                except:
                    show_message("❌ خطا", COLORS["danger"])
            
            return ft.Column([
                ft.Text("📥 ورود کالا", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=15),
                ft.Container(
                    bgcolor=COLORS["bg_card"], border_radius=15, padding=20,
                    content=ft.Column([
                        dropdown,
                        ft.Container(height=10),
                        qty_field,
                        ft.Container(height=15),
                        ft.ElevatedButton("📥 ثبت ورود", on_click=do_buy,
                                        bgcolor=COLORS["success"], color="#fff",
                                        width=300, height=50),
                    ])
                ),
            ])
        
        def build_sell():
            products_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            cart_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            total_text = ft.Text("📦 جمع: 0", size=16, weight=ft.FontWeight.BOLD, 
                                color=COLORS["success"])
            
            def refresh_cart():
                cart_list.controls.clear()
                for i, item in enumerate(cart["items"]):
                    cart_list.controls.append(cart_item_card(item, i))
                if not cart["items"]:
                    cart_list.controls.append(
                        ft.Text("🛒 سبد خالی است", color=COLORS["text_dim"], size=13)
                    )
                total = sum(item["quantity"] for item in cart["items"])
                total_text.value = f"📦 جمع: {total}"
                page.update()
            
            def add_to_cart(product):
                if product["quantity"] <= 0:
                    show_message("❌ موجودی ندارد", COLORS["danger"])
                    return
                for item in cart["items"]:
                    if item["product_id"] == product["id"]:
                        if item["quantity"] >= product["quantity"]:
                            show_message(f"حداکثر: {product['quantity']}", COLORS["warning"])
                            return
                        item["quantity"] += 1
                        refresh_cart()
                        return
                cart["items"].append({
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": 1
                })
                refresh_cart()
            
            def do_finalize(e):
                if not cart["items"]:
                    show_message("❌ سبد خالی است", COLORS["warning"])
                    return
                
                dm.add_transaction(cart["items"], type_="sell")
                total = sum(item["quantity"] for item in cart["items"])
                cart["items"] = []
                refresh_cart()
                show_message(f"✅ فروش ثبت شد ({total} عدد)", COLORS["success"])
                page.views.clear()
                show_main()
            
            # لیست کالاها
            for p in dm.data["products"]:
                if p["quantity"] > 0:
                    products_list.controls.append(
                        ft.Container(
                            bgcolor=COLORS["bg_panel"],
                            border_radius=10,
                            padding=12,
                            margin=ft.margin.only(bottom=5),
                            on_click=lambda e, prod=p: add_to_cart(prod),
                            content=ft.Column([
                                ft.Text(p["name"], size=14, weight=ft.FontWeight.BOLD,
                                       color=COLORS["text"]),
                                ft.Text(f"موجودی: {p['quantity']}", size=11, 
                                       color=COLORS["text_dim"]),
                            ])
                        )
                    )
            
            if not products_list.controls:
                products_list.controls.append(
                    ft.Text("📭 کالایی برای فروش نیست", color=COLORS["text_dim"], size=13)
                )
            
            refresh_cart()
            
            return ft.Column([
                ft.Text("🛒 فروش", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=10),
                ft.Container(
                    bgcolor=COLORS["bg_card"], border_radius=10, padding=10, height=250,
                    content=ft.Column([
                        ft.Text("📦 کالاها (برای افزودن کلیک کنید)", size=12, 
                               color=COLORS["text_dim"]),
                        products_list,
                    ])
                ),
                ft.Container(height=10),
                ft.Container(
                    bgcolor=COLORS["bg_card"], border_radius=10, padding=10, height=200,
                    content=ft.Column([
                        ft.Text("🛒 سبد خرید", size=12, color=COLORS["text_dim"]),
                        cart_list,
                    ])
                ),
                ft.Container(height=10),
                total_text,
                ft.Container(height=5),
                ft.ElevatedButton("✅ نهایی کردن فروش", on_click=do_finalize,
                                bgcolor=COLORS["success"], color="#fff",
                                width=350, height=45),
            ], scroll=ft.ScrollMode.AUTO)
        
        def build_transactions():
            t_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            
            for t in reversed(dm.data["transactions"]):
                is_buy = t["type"] == "buy"
                color = COLORS["success"] if is_buy else COLORS["accent"]
                icon = "📥" if is_buy else "📤"
                type_text = "خرید" if is_buy else "فروش"
                
                items_summary = " | ".join([f"{i.get('product_name', '')} × {i.get('quantity', 0)}" 
                                            for i in t.get("items", [])[:2]])
                
                t_list.controls.append(
                    ft.Container(
                        bgcolor=COLORS["bg_card"], border_radius=10, padding=12,
                        margin=ft.margin.only(bottom=8),
                        content=ft.Row([
                            ft.Text(icon, size=28, color=color),
                            ft.Column([
                                ft.Text(f"{type_text} - {items_summary}", size=13, 
                                       weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                                ft.Text(t["date"][:16].replace("T", " "), size=10, 
                                       color=COLORS["text_dim"]),
                            ], expand=True),
                            ft.Text(f"{t.get('total_quantity', 0)} عدد", size=13, 
                                   weight=ft.FontWeight.BOLD, color=color),
                        ])
                    )
                )
            
            if not dm.data["transactions"]:
                t_list.controls.append(
                    ft.Text("📭 هیچ تراکنشی نیست", color=COLORS["text_dim"], size=13)
                )
            
            return ft.Column([
                ft.Text("📋 تاریخچه", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=15),
                t_list,
            ], expand=True)
        
        def build_reports():
            return ft.Column([
                ft.Text("📈 گزارشات", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=15),
                stat_card("📤", "کل فروش", str(dm.get_total_sold_quantity()), COLORS["accent"]),
                ft.Container(height=8),
                stat_card("📥", "کل خرید", str(dm.get_total_bought_quantity()), COLORS["success"]),
                ft.Container(height=8),
                stat_card("🏪", "موجودی کل", str(dm.get_total_inventory()), COLORS["warning"]),
                ft.Container(height=8),
                stat_card("📦", "تعداد کالاها", str(len(dm.data["products"])), COLORS["text"]),
            ], scroll=ft.ScrollMode.AUTO)
        
        def build_settings():
            username_field = create_field("نام کاربری جدید")
            password_field = create_field("رمز عبور جدید", password=True)
            confirm_field = create_field("تکرار رمز عبور", password=True)
            
            def save_creds(e):
                u = username_field.value.strip()
                p = password_field.value.strip()
                c = confirm_field.value.strip()
                
                if not u or not p:
                    show_message("❌ فیلدها را پر کنید", COLORS["danger"])
                    return
                if p != c:
                    show_message("❌ رمزها یکسان نیستند", COLORS["danger"])
                    return
                if len(p) < 4:
                    show_message("❌ رمز حداقل ۴ کاراکتر", COLORS["danger"])
                    return
                
                dm.change_credentials(u, p)
                show_message("✅ تغییر کرد", COLORS["success"])
                username_field.value = ""
                password_field.value = ""
                confirm_field.value = ""
                page.update()
            
            def do_reset(e):
                dm.reset_all()
                cart["items"] = []
                show_message("✅ همه چیز پاک شد", COLORS["success"])
                page.views.clear()
                show_main()
            
            def confirm_reset(e):
                dialog = ft.AlertDialog(
                    title=ft.Text("⚠️ هشدار", color=COLORS["danger"]),
                    content=ft.Text("آیا مطمئن هستید؟ تمام اطلاعات پاک می‌شود.", 
                                   color=COLORS["text"]),
                    actions=[
                        ft.TextButton("بله، پاک کن", on_click=lambda e: (close_dialog(dialog), do_reset(e))),
                        ft.TextButton("انصراف", on_click=lambda e: close_dialog(dialog)),
                    ],
                )
                page.overlay.append(dialog)
                dialog.open = True
                page.update()
            
            return ft.Column([
                ft.Text("⚙️ تنظیمات", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=15),
                ft.Container(
                    bgcolor=COLORS["bg_card"], border_radius=15, padding=20,
                    content=ft.Column([
                        ft.Text("🔐 تغییر نام کاربری و رمز", size=16, 
                               weight=ft.FontWeight.BOLD, color=COLORS["accent"]),
                        ft.Container(height=10),
                        username_field,
                        ft.Container(height=8),
                        password_field,
                        ft.Container(height=8),
                        confirm_field,
                        ft.Container(height=15),
                        ft.ElevatedButton("💾 ذخیره", on_click=save_creds,
                                        bgcolor=COLORS["accent"], color="#fff",
                                        width=300, height=45),
                    ])
                ),
                ft.Container(height=15),
                ft.Container(
                    bgcolor=COLORS["bg_card"], border_radius=15, padding=20,
                    content=ft.Column([
                        ft.Text("⚠️ منطقه خطر", size=16, 
                               weight=ft.FontWeight.BOLD, color=COLORS["danger"]),
                        ft.Container(height=10),
                        ft.Text("تمام اطلاعات پاک می‌شود", size=12, color=COLORS["text_dim"]),
                        ft.Container(height=15),
                        ft.ElevatedButton("🗑️ ریست کامل", on_click=confirm_reset,
                                        bgcolor=COLORS["danger"], color="#fff",
                                        width=300, height=45),
                    ])
                ),
            ], scroll=ft.ScrollMode.AUTO)
        
        # ===== ناوبری =====
        def navigate(page_name):
            content_area.content = pages[page_name]()
            page.update()
        
        pages = {
            "dashboard": build_dashboard,
            "products": build_products,
            "buy": build_buy,
            "sell": build_sell,
            "transactions": build_transactions,
            "reports": build_reports,
            "settings": build_settings,
        }
        
        # ===== نوار پایین =====
        nav_bar = ft.Container(
            bgcolor=COLORS["bg_panel"],
            padding=ft.padding.symmetric(vertical=8),
            content=ft.Row(
                controls=[
                    nav_btn("📊", "داشبورد", lambda e: navigate("dashboard")),
                    nav_btn("📦", "کالاها", lambda e: navigate("products")),
                    nav_btn("📥", "ورود", lambda e: navigate("buy")),
                    nav_btn("🛒", "فروش", lambda e: navigate("sell")),
                    nav_btn("📋", "تاریخچه", lambda e: navigate("transactions")),
                    nav_btn("📈", "گزارش", lambda e: navigate("reports")),
                    nav_btn("⚙️", "تنظیمات", lambda e: navigate("settings")),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        
        # ===== ساخت صفحه اصلی =====
        navigate("dashboard")
        
        main_view = ft.View(
            route="/",
            bgcolor=COLORS["bg_dark"],
            padding=0,
            controls=[
                ft.Column([
                    content_area,
                    nav_bar,
                ], expand=True, spacing=0)
            ],
        )
        
        page.views.append(main_view)
        page.update()
    
    # ==================== کامپوننت‌های کمکی ====================
    def stat_card(icon, title, value, color):
        return ft.Container(
            bgcolor=COLORS["bg_card"],
            border_radius=15,
            padding=15,
            expand=True,
            content=ft.Column([
                ft.Text(icon, size=28),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(title, size=12, color=COLORS["text_dim"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        )
    
    def low_stock_card(product):
        return ft.Container(
            bgcolor=COLORS["bg_panel"],
            border_radius=10,
            padding=12,
            margin=ft.margin.only(bottom=5),
            content=ft.Row([
                ft.Text(product["name"], size=14, weight=ft.FontWeight.BOLD, 
                       color=COLORS["text"], expand=True),
                ft.Text(f"موجودی: {product['quantity']}", size=12, color=COLORS["danger"]),
            ])
        )
    
    def product_card(product):
        def delete(e):
            dm.delete_product(product["id"])
            page.views.clear()
            show_main()
            show_message("🗑️ کالا حذف شد", COLORS["warning"])
        
        return ft.Container(
            bgcolor=COLORS["bg_card"],
            border_radius=12,
            padding=15,
            margin=ft.margin.only(bottom=8),
            content=ft.Row([
                ft.Column([
                    ft.Text(product["name"], size=15, weight=ft.FontWeight.BOLD, 
                           color=COLORS["text"]),
                    ft.Text(f"دسته: {product.get('category', '-')}", size=11, 
                           color=COLORS["text_dim"]),
                ], expand=True),
                ft.Column([
                    ft.Text(f"{product['quantity']}", size=22, weight=ft.FontWeight.BOLD,
                           color=COLORS["success"] if product["quantity"] > 3 else COLORS["danger"]),
                    ft.Text("موجودی", size=10, color=COLORS["text_dim"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.IconButton(ft.Icons.DELETE, icon_color=COLORS["danger"], on_click=delete),
            ])
        )
    
    def cart_item_card(item, index):
        def inc(e):
            product = dm.get_product(item["product_id"])
            if item["quantity"] < product["quantity"]:
                item["quantity"] += 1
                page.views.clear()
                show_main()
        
        def dec(e):
            if item["quantity"] > 1:
                item["quantity"] -= 1
                page.views.clear()
                show_main()
            else:
                cart["items"].pop(index)
                page.views.clear()
                show_main()
        
        return ft.Container(
            bgcolor=COLORS["bg_panel"],
            border_radius=8,
            padding=8,
            margin=ft.margin.only(bottom=4),
            content=ft.Row([
                ft.Text(item["product_name"], size=12, color=COLORS["text"], expand=True),
                ft.IconButton(ft.Icons.ADD, icon_size=18, on_click=inc, 
                             icon_color=COLORS["accent"]),
                ft.Text(str(item["quantity"]), size=13, weight=ft.FontWeight.BOLD,
                       color=COLORS["text"]),
                ft.IconButton(ft.Icons.REMOVE, icon_size=18, on_click=dec,
                             icon_color=COLORS["warning"]),
            ])
        )
    
    def nav_btn(icon, label, on_click):
        return ft.Container(
            content=ft.Column([
                ft.Text(icon, size=20),
                ft.Text(label, size=9, color=COLORS["text_dim"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            on_click=on_click,
            padding=5,
            border_radius=8,
            ink=True,
        )
    
    def close_dialog(dialog):
        dialog.open = False
        page.update()
    
    # ==================== شروع ====================
    show_login()


ft.app(target=main)
