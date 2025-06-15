# FamilyChef – H5 Cooking-Assistant  
A Django-powered mobile web (“H5”) application that helps families plan, cook, and restock ingredients with minimal friction.

---

## 1 . Product Vision
Give every home a lightweight “back-of-house” system:

1. **Order** – Any family member can browse the family menu, see what can be cooked *now* (ingredients in stock are highlighted) and place an order.
2. **Cook / Menu Maintenance** – The home chef records or edits recipes: required ingredients, allowed substitutions, and standard cooking time.
3. **Shop / Stock** – The pantry level is monitored; low-stock or expired items trigger warnings, and the family updates inventory after shopping.

---

## 2 . Personas & Core Scenarios
| Persona | Goals | Key Scenario |
|---------|-------|--------------|
| Hungry Member | Eat quickly, know what’s available | “Ordering” |
| Home Chef | Keep recipes organized, know what to cook next | “Menu” + “Order board” |
| Shopper | Avoid out-of-stock surprises, minimise waste | “Shopping” |

---

## 3 . User Flow (Happy Path)
1. Chef maintains menu (adds “Beef Curry” → beef 200 g, potato 2, carrots 1, any oil, 45 min).  
2. Inventory currently has beef 500 g, potato 4, carrot 0.  
3. Another member opens Ordering page → “Beef Curry” shown in **grey** (missing carrots).  
4. Member chooses “Tomato & Egg” (all in stock) → order created, chef notified.  
5. Beef and carrots reach threshold → Shopper sees warning and buys items → updates stock.

---

## 4 . Architecture High-Level

```
┌──────────┐   REST/WS   ┌──────────────┐     localStorage/
│  Front-  │◄──────────►│  Django API  │◄───► IndexedDB
│   end    │  JSON/Web  │              │     (offline cache)
└──────────┘  Socket    └─────┬────────┘
                              │Celery (cron/async)
                    ┌─────────▼─────────┐
                    │  PostgreSQL DB    │
                    └───────────────────┘
```

Frontend can be: Vue 3/Quasar, React + Vite, or plain JS + Tailwind – choose what your team knows best.  
Backend: Django 5.x, Django REST Framework, Channels (WebSocket), Celery + Redis for jobs.

---

## 5 . Data Model (ER diagram excerpt)

```
User
└─► Family (M2M through FamilyMember)

Cuisine                    Ingredient
└─1:M─ RecipeIngredient ─M:┘
Cuisine fields: name, default_time_min
RecipeIngredient: qty, unit, is_optional, is_substitutable

PantryStock
ingredient FK, qty_available, unit, best_before

Order
family FK, cuisine FK, created_by, status [NEW, COOKING, DONE], scheduled_for
OrderItemIngredient (snapshot for historical accuracy)

ShoppingList
ingredient FK, qty_needed, created_at, resolved_at
```

---

## 6 . API Sketch (Django REST Framework)

| Verb & Path | Description |
|-------------|-------------|
| `GET /api/menu/` | List cuisines (+ availability flag) |
| `POST /api/orders/` | Place new order |
| `PATCH /api/orders/{id}/status/` | Chef updates status |
| `POST /api/cuisines/` | Add/update recipe |
| `GET /api/pantry/` / `PATCH` | View & adjust stock |
| `GET /api/alerts/` | Low-stock / expiry notifications |

WebSocket channel `/ws/orders/{family_id}/` pushes real-time order updates to chef dashboard.

---

## 7 . Key Backend Logic
1. **Availability Engine**  
   For each cuisine:  
   `is_available = all(required_qty <= stock_qty or substitutable_found)`  
   Run on-demand & nightly batch (Celery) to pre-cache results.

2. **Low-Stock Detection**  
   Celery beat job daily:  
   - Threshold % per ingredient (configurable)  
   - Expired items (`best_before < today`)  
   Emit Alert objects → push & e-mail.

3. **Order Fulfilment**  
   When chef sets status = DONE → automatically deduct used quantities from PantryStock.

---

## 8 . Frontend Pages
1. Login / Family switch (JWT in localStorage)  
2. Ordering  
   - Menu grid, colour-coded availability  
   - Search / filter, favourites  
3. Chef Board  
   - “Incoming orders” Kanban (NEW → COOKING → DONE)  
   - One-tap start / finish  
4. Menu Editor  
   - CRUD cuisines, drag-drop ingredient list, optional substitutes  
5. Pantry & Shopping  
   - Current stock list, simple +/- adjust  
   - Auto-generated “Need to buy” list, mark items acquired

Responsive layout: 1-column on ≤480 px, 2-column tablets, dark mode optional.

---

## 9 . Non-Functional Requirements
• PWA support: add-to-home-screen, offline cache of menu  
• Auth: Django AllAuth + JWT; one user can belong to multiple families  
• i18n: at least EN/zh-CN JSON bundles  
• Unit tests ≥80 % coverage, Cypress e2e  
• CI/CD: GitHub Actions → Docker build → Fly.io / Dokku

---

## 10 . Milestone Plan

| Phase | Deliverables | Duration |
|-------|--------------|----------|
| 0. Setup | Repo, Docker compose (Django, PostgreSQL, Redis) | 0.5 wk |
| 1. Core Models & APIs | User, Family, Ingredient, Cuisine, PantryStock | 1.5 wk |
| 2. Ordering Flow | Menu availability calc, order CRUD, WebSocket push | 1 wk |
| 3. Chef & Pantry | Order board, stock deduction, low-stock alerts | 1 wk |
| 4. Shopping List | Auto list, manual resolve, push notify | 0.5 wk |
| 5. Polish & PWA | Offline menu, add-to-home, responsive UI | 1 wk |
| 6. Tests + CI/CD | 80 % backend, 20 e2e; auto deploy staging | 0.5 wk |
| 7. Pilot | Onboard a real family, gather feedback | 1 wk |

Total ≈ 7 weeks.

---

## 11 . Future Ideas
• Barcode scan to input groceries  
• Nutrition & cost tracking  
• Voice assistant (“Hey Chef, what can I cook?”)  
• Social recipe sharing across families

---

Happy cooking!
