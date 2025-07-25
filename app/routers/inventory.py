from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case
from datetime import date, datetime
from typing import Optional
from app.database import get_db
from app.models.models import Inventory, User, InventoryItemType
from app.auth import get_current_user_from_cookie, get_admin_user
from app.file_manager import file_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def can_edit_inventory(current_user: User, item: Inventory) -> bool:
    """Проверяет, может ли пользователь редактировать предмет инвентаря"""
    # Админы могут редактировать всё
    if current_user.is_admin == 1:
        return True
    
    # Создатель (автор) записи может редактировать (включая клубные предметы)
    if item.created_by_user_id == current_user.id:
        return True
    
    # Для клубных предметов - только автор и админы могут редактировать
    if item.is_club_item:
        return False  # Уже проверили админа и автора выше
    
    # Для обычных предметов - владелец может редактировать
    # Проверяем owner_user_id
    if item.owner_user_id == current_user.id:
        return True
    
    # Для старых записей без owner_user_id проверяем по имени владельца
    if item.owner_user_id is None and item.created_by_user_id is None:
        # Для VK пользователей проверяем полное имя
        if current_user.vk_id:
            user_full_name = f"{current_user.first_name} {current_user.last_name}".strip()
            if user_full_name and item.owner == user_full_name:
                return True
        
        # Для обычных пользователей проверяем username
        if item.owner == current_user.username:
            return True
    
    return False

@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db),
    owner: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    material: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    club_items: Optional[str] = Query(None)
):
    # Базовый запрос с LEFT JOIN для получения данных владельца
    query = db.query(Inventory).outerjoin(User, Inventory.owner_user_id == User.id)
    
    # Применяем фильтры
    if owner and owner != "all":
        # Поиск по имени пользователя (для обратной совместимости со старыми записями)
        query = query.filter(
            (Inventory.owner == owner) |  # Старые записи
            (User.username == owner) |   # По username
            (func.concat(User.first_name, ' ', User.last_name) == owner)  # По полному имени VK
        )
    if item_type and item_type != "all":
        # Фильтрация по новому полю item_type_id
        try:
            item_type_id = int(item_type)
            query = query.filter(Inventory.item_type_id == item_type_id)
        except ValueError:
            # Если передан не ID, а текст - используем старое поле для обратной совместимости
            query = query.filter(Inventory.item_type == item_type)
    if material and material != "all":
        query = query.filter(Inventory.material == material)
    
    # Обработка фильтра клубных предметов
    if club_items and club_items.strip():
        if club_items.lower() == "true":
            query = query.filter(Inventory.is_club_item == True)
        elif club_items.lower() == "false":
            query = query.filter(Inventory.is_club_item == False)
    
    if search:
        query = query.filter(
            (Inventory.item_name.ilike(f"%{search}%")) |
            (Inventory.owner.ilike(f"%{search}%")) |  # Поиск по старому полю
            (User.username.ilike(f"%{search}%")) |    # Поиск по username
            (func.concat(User.first_name, ' ', User.last_name).ilike(f"%{search}%")) |  # Поиск по полному имени
            (Inventory.notes.ilike(f"%{search}%")) |
            (Inventory.material.ilike(f"%{search}%"))
        )
    
    # Исправленный ORDER BY - простая сортировка без nullslast
    inventory_items_raw = query.order_by(
        Inventory.owner,
        Inventory.item_name
    ).all()
    
    # Обрабатываем результаты для правильного отображения владельца
    inventory_items = []
    for item in inventory_items_raw:
        # ИСПРАВЛЕНИЕ: всегда используем строковое поле owner для отображения
        # Это поле уже содержит правильное имя владельца
        inventory_items.append(item)
    
    # ИСПРАВЛЕНИЕ: используем только поле owner из таблицы inventory для единообразия
    owners_query = text('''
        SELECT DISTINCT owner as owner_name 
        FROM inventory
        WHERE owner IS NOT NULL AND owner != ''
        ORDER BY owner
    ''')
    owners_list = db.execute(owners_query).fetchall()
    
    # ИСПРАВЛЕНИЕ: используем справочник типов, но только те, которые есть в инвентаре
    types_list_query = text('''
        SELECT DISTINCT iit.id, iit.name, iit.sort_order
        FROM inventory_item_types iit
        INNER JOIN inventory i ON i.item_type_id = iit.id
        WHERE iit.is_active = true
        ORDER BY iit.sort_order, iit.name
    ''')
    types_list_raw = db.execute(types_list_query).fetchall()
    
    # Преобразуем в нужный формат для шаблона: (id, name)
    types_list = [(str(row[0]), row[1]) for row in types_list_raw]
    
    materials_list = db.query(Inventory.material).distinct().filter(Inventory.material.isnot(None)).order_by(Inventory.material).all()
    
    # Статистика
    total_items = db.query(func.count(Inventory.id)).scalar()
    club_items_count = db.query(func.count(Inventory.id)).filter(Inventory.is_club_item == True).scalar()
    
    # Подсчет уникальных владельцев (учитываем и старые и новые записи)
    unique_owners_query = text('''
        SELECT COUNT(DISTINCT owner_name) 
        FROM (
            SELECT COALESCE(u.username, i.owner) as owner_name
            FROM inventory i
            LEFT JOIN users u ON i.owner_user_id = u.id
        ) owners
    ''')
    unique_owners = db.execute(unique_owners_query).scalar()
    
    return templates.TemplateResponse("inventory/list.html", {
        "request": request,
        "user": current_user,
        "inventory_items": inventory_items,
        "owners_list": owners_list,
        "types_list": types_list,
        "materials_list": materials_list,
        "total_items": total_items,
        "club_items_count": club_items_count,
        "unique_owners": unique_owners,
        "filters": {
            "owner": owner,
            "item_type": item_type,
            "material": material,
            "search": search,
            "club_items": club_items
        }
    })

@router.get("/inventory/add", response_class=HTMLResponse)
async def add_inventory_page(
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    owner_preset: bool = Query(False)  # Параметр для автозаполнения владельца
):
    # Определяем имя пользователя для автозаполнения
    user_display_name = ""
    is_vk_user = bool(current_user.vk_id)
    is_admin = current_user.is_admin == 1
    
    if current_user.vk_id:  # VK пользователь
        user_display_name = f"{current_user.first_name} {current_user.last_name}".strip()
        if not user_display_name:
            user_display_name = current_user.username
    else:  # Обычный пользователь
        user_display_name = current_user.username
    
    # Получаем типы предметов из справочника
    item_types = db.query(InventoryItemType).filter(InventoryItemType.is_active == True).order_by(InventoryItemType.sort_order, InventoryItemType.name).all()
    
    # Получаем материалы из справочника
    from app.models.models import InventoryMaterialType
    material_types = db.query(InventoryMaterialType).filter(InventoryMaterialType.is_active == True).order_by(InventoryMaterialType.sort_order, InventoryMaterialType.name).all()

    # Группируем материалы по категориям
    from collections import defaultdict
    materials_by_category = defaultdict(list)
    for material in material_types:
        materials_by_category[material.category or "Без категории"].append(material)

    return templates.TemplateResponse("inventory/add.html", {
        "request": request,
        "user": current_user,
        "user_display_name": user_display_name,
        "is_vk_user": is_vk_user,
        "is_admin": is_admin,
        "owner_preset": owner_preset,
        "item_types": item_types,
        # "material_types": material_types,  # больше не нужно
        "materials_by_category": materials_by_category
    })

@router.post("/inventory/add")
async def add_inventory(
    request: Request,
    owner: str = Form(...),
    item_name: str = Form(...),
    item_type: Optional[str] = Form(None),
    subtype: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    material_type: Optional[str] = Form(None),  # Новое поле для ID материала
    color: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    find_type: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    burial_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    is_club_item: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        # Обрабатываем изображение если есть
        image_data = None
        image_filename = None
        image_size = None
        
        if image and image.filename:
            # Сохраняем в base64 для надежности
            image_data, image_filename, image_size = await file_manager.save_inventory_image_to_base64(image)
        
        # Определяем владельца
        owner_user_id = None
        final_owner = owner  # Для обратной совместимости оставляем строковое поле
        
        if is_club_item:
            # Клубный предмет - владелец "Клуб", owner_user_id = None
            final_owner = "Клуб"
            owner_user_id = None
        else:
            # Личный предмет - устанавливаем текущего пользователя как владельца
            owner_user_id = current_user.id
            # Для строкового поля используем введенное имя или имя пользователя
            if not owner.strip():
                if current_user.vk_id:
                    final_owner = f"{current_user.first_name} {current_user.last_name}".strip()
                else:
                    final_owner = current_user.username
        
        # Обрабатываем материал
        material_type_id = None
        material_name = None
        
        if material_type:
            try:
                material_type_id = int(material_type)
                # Получаем название материала из справочника
                from app.models.models import InventoryMaterialType
                material_obj = db.query(InventoryMaterialType).filter(InventoryMaterialType.id == material_type_id).first()
                if material_obj:
                    material_name = material_obj.name
            except ValueError:
                pass
        
        inventory_item = Inventory(
            owner=final_owner,
            owner_user_id=owner_user_id,
            item_name=item_name,
            item_type=item_type if item_type else None,
            subtype=subtype if subtype else None,
            material=material_name if material_name else material,  # Используем название из справочника или введенное вручную
            material_type_id=material_type_id,  # Новое поле
            color=color if color else None,
            size=size if size else None,
            find_type=find_type if find_type else None,
            region=region if region else None,
            place=place if place else None,
            burial_number=burial_number if burial_number else None,
            notes=notes if notes else None,
            is_club_item=is_club_item,
            # Новые поля для base64 хранения
            image_data=image_data,
            image_filename=image_filename,
            image_size=image_size,
            created_by_user_id=current_user.id
        )
        
        db.add(inventory_item)
        db.commit()
        
        return RedirectResponse(url="/inventory", status_code=302)
        
    except HTTPException as e:
        db.rollback()  # Откатываем транзакцию при ошибке
        return templates.TemplateResponse("inventory/add.html", {
            "request": request,
            "user": current_user,
            "error": e.detail
        })
    except Exception as e:
        db.rollback()  # Откатываем транзакцию при ошибке
        return templates.TemplateResponse("inventory/add.html", {
            "request": request,
            "user": current_user,
            "error": f"Произошла ошибка: {str(e)}"
        })

@router.get("/inventory/edit/{item_id}", response_class=HTMLResponse)
async def edit_inventory_page(
    item_id: int, 
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    # Проверяем права доступа
    if not can_edit_inventory(current_user, item):
        return templates.TemplateResponse("inventory/edit.html", {
            "request": request,
            "user": current_user,
            "item": item,
            "error": "У вас нет прав для редактирования этого предмета. Только владелец или администратор может редактировать предмет."
        })
    
    return templates.TemplateResponse("inventory/edit.html", {
        "request": request,
        "user": current_user,
        "item": item
    })

@router.post("/inventory/edit/{item_id}")
async def edit_inventory(
    item_id: int,
    request: Request,
    owner: str = Form(...),
    item_name: str = Form(...),
    item_type: Optional[str] = Form(None),
    subtype: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    find_type: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    burial_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    is_club_item: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    # Проверяем права доступа
    if not can_edit_inventory(current_user, item):
        return templates.TemplateResponse("inventory/edit.html", {
            "request": request,
            "user": current_user,
            "item": item,
            "error": "У вас нет прав для редактирования этого предмета."
        })
    
    try:
        # Обрабатываем изображение
        if remove_image:
            # Удаляем изображение из БД
            item.image_data = None
            item.image_filename = None
            item.image_size = None
            # Также удаляем старый файл если есть
            if item.image_path:
                file_manager.delete_file(item.image_path)
                item.image_path = None
        elif image and image.filename:
            # Сохраняем новое изображение в base64
            image_data, image_filename, image_size = await file_manager.save_inventory_image_to_base64(image)
            item.image_data = image_data
            item.image_filename = image_filename
            item.image_size = image_size
            # Удаляем старое изображение если есть
            if item.image_path:
                file_manager.delete_file(item.image_path)
                item.image_path = None
        
        # Если клубный предмет, то владелец всегда "Клуб"
        final_owner = "Клуб" if is_club_item else owner
        
        # Обновляем данные
        item.owner = final_owner
        item.item_name = item_name
        item.item_type = item_type if item_type else None
        item.subtype = subtype if subtype else None
        item.material = material if material else None
        item.color = color if color else None
        item.size = size if size else None
        item.find_type = find_type if find_type else None
        item.region = region if region else None
        item.place = place if place else None
        item.burial_number = burial_number if burial_number else None
        item.notes = notes if notes else None
        item.is_club_item = is_club_item
        # updated_at будет автоматически установлено базой данных
        
        db.commit()
        
        return RedirectResponse(url="/inventory", status_code=302)
        
    except HTTPException as e:
        db.rollback()  # Откатываем транзакцию при ошибке
        return templates.TemplateResponse("inventory/edit.html", {
            "request": request,
            "user": current_user,
            "item": item,
            "error": e.detail
        })
    except Exception as e:
        db.rollback()  # Откатываем транзакцию при ошибке
        return templates.TemplateResponse("inventory/edit.html", {
            "request": request,
            "user": current_user,
            "item": item,
            "error": f"Произошла ошибка: {str(e)}"
        })

@router.post("/inventory/delete/{item_id}")
async def delete_inventory(
    item_id: int, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    # Проверяем права доступа (только владелец или админ)
    if not can_edit_inventory(current_user, item):
        raise HTTPException(status_code=403, detail="У вас нет прав для удаления этого предмета")
    
    # Удаляем изображение если есть
    if item.image_path:
        file_manager.delete_file(item.image_path)
    
    db.delete(item)
    db.commit()
    
    return RedirectResponse(url="/inventory", status_code=302)

@router.get("/inventory/summary", response_class=HTMLResponse)
async def inventory_summary(
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    # Получаем данные по владельцам с разделением на клубные и личные
    summary_query = text('''
        SELECT 
            owner,
            COUNT(*) as item_count,
            COUNT(CASE WHEN is_club_item = true THEN 1 END) as club_items,
            COUNT(CASE WHEN is_club_item = false OR is_club_item IS NULL THEN 1 END) as personal_items,
            ARRAY_TO_STRING(ARRAY_AGG(item_name ORDER BY item_name), ', ') as items
        FROM inventory 
        GROUP BY owner
        ORDER BY owner
    ''')
    
    summary_results = db.execute(summary_query).fetchall()
    
    # Статистика по типам предметов
    types_query = text('''
        SELECT item_type, COUNT(*) as count
        FROM inventory 
        WHERE item_type IS NOT NULL
        GROUP BY item_type
        ORDER BY count DESC
    ''')
    
    types_results = db.execute(types_query).fetchall()
    
    # Статистика по материалам
    materials_query = text('''
        SELECT material, COUNT(*) as count
        FROM inventory 
        WHERE material IS NOT NULL AND material != ''
        GROUP BY material
        ORDER BY count DESC
    ''')
    
    materials_results = db.execute(materials_query).fetchall()
    
    # Статистика клубного имущества
    club_stats = db.execute(text('''
        SELECT 
            COUNT(*) as total_club_items,
            COUNT(DISTINCT owner) as club_item_owners
        FROM inventory 
        WHERE is_club_item = true
    ''')).fetchone()
    
    return templates.TemplateResponse("inventory/summary.html", {
        "request": request,
        "user": current_user,
        "summary_results": summary_results,
        "types_results": types_results,
        "materials_results": materials_results,
        "club_stats": club_stats
    })

@router.get("/inventory/{item_id}", response_class=HTMLResponse)
async def view_inventory_item(
    item_id: int, 
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    # Показываем только предметы того же владельца (исправлено)
    similar_items = db.query(Inventory).filter(
        Inventory.owner == item.owner,
        Inventory.id != item.id
    ).limit(5).all()
    
    # Проверяем права на редактирование
    can_edit = can_edit_inventory(current_user, item)
    
    # Получаем информацию об авторе записи
    author = None
    if item.created_by_user_id:
        author = db.query(User).filter(User.id == item.created_by_user_id).first()
    
    return templates.TemplateResponse("inventory/detail.html", {
        "request": request,
        "user": current_user,
        "item": item,
        "similar_items": similar_items,
        "can_edit": can_edit,
        "author": author
    })

# Новый роут для миграции данных (только для админов)
@router.post("/inventory/migrate-club-items")
async def migrate_club_items(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Миграция: добавляет клубный инвентарь и владельца 'Эрен'"""
    
    # Помечаем предметы с владельцем "Клуб" как клубные
    club_items = db.query(Inventory).filter(Inventory.owner == "Клуб").all()
    for item in club_items:
        item.is_club_item = True
    
    # Помечаем часть предметов Эрена как клубные (например, те что в notes содержат "клуб")
    eren_club_items = db.query(Inventory).filter(
        Inventory.owner == "Эрен",
        Inventory.notes.ilike("%клуб%")
    ).all()
    for item in eren_club_items:
        item.is_club_item = True
    
    db.commit()
    
    return {"message": f"Помечено {len(club_items) + len(eren_club_items)} предметов как клубные"}

# Роут для пакетного обновления создателей (миграция)
@router.post("/inventory/migrate-creators")
async def migrate_creators(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Миграция: устанавливает создателя для всех предметов без created_by_user_id"""
    
    # Назначаем текущего админа создателем всех предметов без создателя
    items_without_creator = db.query(Inventory).filter(Inventory.created_by_user_id.is_(None)).all()
    
    for item in items_without_creator:
        item.created_by_user_id = current_user.id
        item.created_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Назначен создатель для {len(items_without_creator)} предметов"} 