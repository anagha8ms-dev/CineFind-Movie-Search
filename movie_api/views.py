
import requests

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Watchlist


TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


@require_GET
def search_movie(request):
    title = request.GET.get("title", "").strip()

    if not title:
        return JsonResponse(
            {"error": "Please enter a movie name."},
            status=400,
        )

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={
                "api_key": settings.TMDB_API_KEY,
                "query": title,
                "language": "en-US",
                "include_adult": "false",
            },
            timeout=10,
        )
        response.raise_for_status()
        return JsonResponse(response.json())

    except requests.RequestException:
        return JsonResponse(
            {"error": "Unable to connect to TMDB."},
            status=502,
        )


def get_movies(endpoint, params):
    response = requests.get(
        f"{TMDB_BASE_URL}/{endpoint}",
        params={
            "api_key": settings.TMDB_API_KEY,
            **params,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def add_poster_urls(movies):
    for movie in movies:
        poster_path = movie.get("poster_path")
        movie["poster_url"] = (
            f"{IMAGE_BASE_URL}{poster_path}"
            if poster_path else None
        )
    return movies


def home(request):
    title = request.GET.get("title", "").strip()

    try:
        page = max(1, int(request.GET.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    page = min(page, 500)

    movies = []
    popular_movies = []
    error = ""
    total_pages = 1

    try:
        if title:
            data = get_movies(
                "search/movie",
                {
                    "query": title,
                    "include_adult": False,
                    "language": "en-US",
                    "page": page,
                },
            )

            movies = add_poster_urls(
                data.get("results", [])
            )

        else:
            data = get_movies(
                "discover/movie",
                {
                    "with_original_language": "ml",
                    "sort_by": "popularity.desc",
                    "include_adult": False,
                    "language": "en-US",
                    "page": page,
                },
            )

            popular_movies = add_poster_urls(
                data.get("results", [])
            )

        total_pages = min(
            data.get("total_pages", 1),
            500
        )

        if title and not movies:
            error = "No movies found. Try another title."

    except requests.HTTPError as e:
        print("TMDB HTTP ERROR:", e.response.status_code)
        print("TMDB RESPONSE:", e.response.text)
        error = f"TMDB API error: {e.response.status_code}"

    except requests.RequestException as e:
        print("TMDB CONNECTION ERROR:", repr(e))
        error = "Unable to connect to TMDB. Check your internet."

    except (ValueError, KeyError, TypeError) as e:
        print("TMDB DATA ERROR:", repr(e))
        error = "Unable to process movie data."

    page_numbers = range(
        max(1, page - 2),
        min(total_pages, page + 2) + 1
    )

    return render(
        request,
        "index.html",
        {
            "title": title,
            "movies": movies,
            "popular_movies": popular_movies,
            "error": error,
            "page": page,
            "total_pages": total_pages,
            "page_numbers": page_numbers,
        },
    )

def movie_details(request, movie_id):
    movie = None
    error = ""

    try:
        movie = get_movies(
            f"movie/{movie_id}",
            {"language": "en-US"},
        )

        poster_path = movie.get("poster_path")
        movie["poster_url"] = (
            f"{IMAGE_BASE_URL}{poster_path}"
            if poster_path else None
        )

    except (requests.RequestException, ValueError):
        error = "Movie details could not be loaded."

    return render(
        request,
        "movie_details.html",
        {
            "movie": movie,
            "error": error,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = AuthenticationForm(
        request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("home")

    return render(request, "login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)

    return redirect("home")


@login_required
def add_to_watchlist(request, movie_id):
    if request.method != "POST":
        return redirect("home")

    try:
        movie = get_movies(
            f"movie/{movie_id}",
            {"language": "en-US"},
        )

    except (requests.RequestException, ValueError):
        messages.error(request, "Unable to load movie details.")
        return redirect("home")

    Watchlist.objects.get_or_create(
        user=request.user,
        movie_id=movie["id"],
        defaults={
            "title": movie.get("title", "Untitled movie"),
            "poster_path": movie.get("poster_path"),
            "release_date": movie.get("release_date", ""),
        },
    )

    messages.success(request, "Movie saved to your watchlist!")

    return redirect("movie_details", movie_id=movie_id)


@login_required
def my_watchlist(request):
    movies = Watchlist.objects.filter(user=request.user)

    return render(
        request,
        "watchlist.html",
        {"movies": movies},
    )


@login_required
def remove_from_watchlist(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(
            Watchlist,
            id=item_id,
            user=request.user,
        )
        item.delete()
        messages.success(request, "Movie removed from watchlist.")

    return redirect("my_watchlist")

@login_required
def profile_view(request):
    return render(request,'profile.html')
