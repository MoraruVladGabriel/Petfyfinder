from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q

from .forms import NewItemForm, EditItemForm
from .models import Item, Category

from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import networkx as nx # type: ignore

# Create your views here.

@login_required
def items(request):
    query = request.GET.get('query', '')
    category_id = request.GET.get('category', 0)
    sort = request.GET.get('sort', '')
    categories = Category.objects.all()
    items = Item.objects.filter(is_adopted=False)

    if category_id:
        items = items.filter(category_id=category_id)

    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if sort == 'crescator':
        items = get_sorted_items(request.user, False)
    else: 
        if sort == 'descrescator':
            items = get_sorted_items(request.user, True)

    return render(request, 'item/items.html', {
        'items': items,
        'query': query,
        'categories': categories,
        'category_id': int(category_id),
    })

def calculate_distance(loc1, loc2):
    return geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).kilometers

def create_graph(items, user_location):
    G = nx.Graph()

    G.add_node("user", pos=(user_location.latitude, user_location.longitude))
    for item in items:
        geolocator = Nominatim(user_agent="myApp", timeout=10)
        item_location = geolocator.geocode(item.location)
        G.add_node(item.id, pos=(item_location.latitude, item_location.longitude))

    for item in items:
        geolocator = Nominatim(user_agent="myApp", timeout=10)
        item_location = geolocator.geocode(item.location)
        distance = calculate_distance(user_location, item_location)
        G.add_edge("user", item.id, weight=distance)

    return G

def get_sorted_items(user, type):
    geolocator = Nominatim(user_agent="myApp", timeout=10)
    user_location = geolocator.geocode(user.profile.location)
    items = Item.objects.filter(is_adopted=False)
    G = create_graph(items, user_location)

    # Calculează distanțele folosind algoritmul lui Dijkstra
    distances = nx.single_source_dijkstra_path_length(G, "user")
    
    # Sortează animalele de companie pe baza distanțelor
    sorted_items = sorted(items, key=lambda item: distances[item.id], reverse=type)
    
    return sorted_items

def detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    related_items = Item.objects.filter(category=item.category, is_adopted=False).exclude(pk=pk)[0:3]

    return render(request, 'item/detail.html', {
        'item': item,
        'related_items': related_items,
    })

@login_required
def new(request):
    if request.method == 'POST':
        form = NewItemForm(request.POST, request.FILES)

        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()

            return redirect('item:detail', pk=item.id)
    else:
        form = NewItemForm()

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'New item',
    })

@login_required
def edit(request, pk):
    item = get_object_or_404(Item, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = EditItemForm(request.POST, request.FILES, instance=item)

        if form.is_valid():
            form.save()

            return redirect('item:detail', pk=item.id)
    else:
        form = EditItemForm(instance=item)

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'Edit item',
    })

@login_required
def delete(request, pk):
    item = get_object_or_404(Item, pk=pk, created_by=request.user)
    item.delete()

    return redirect('dashboard:index')
