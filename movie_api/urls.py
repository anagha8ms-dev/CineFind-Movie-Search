from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search_movie, name="search_movie"),

    path(
        "details/<int:movie_id>/",
        views.movie_details,
        name="movie_details",
    ),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("watchlist/", views.my_watchlist, name="my_watchlist"),
    path("watchlist/remove/<int:item_id>/",views.remove_from_watchlist,name="remove_from_watchlist"),
    path("watchlist/add/<int:movie_id>/",views.add_to_watchlist,name="add_to_watchlist"),
    path('profile/',views.profile_view,name='profile'),
]