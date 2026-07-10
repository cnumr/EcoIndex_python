example_ecoindex_not_found = {
    "description": "Not found",
    "content": {
        "application/json": {
            "example": {
                "detail": (
                    "Analysis e9a4d5ea-b9c5-4440-a74a-cac229f7d672 "
                    "not found for version v1"
                )
            }
        }
    },
}

example_file_not_found = {
    "description": "Not found",
    "content": {
        "application/json": {
            "example": {
                "detail": (
                    "Screenshot v1/"
                    "550cdf8c-9c4c-4f8a-819d-cb69d0866fe1.webp does not exist."
                )
            }
        }
    },
}

example_page_listing_empty = {
    "description": "Empty page",
    "content": {
        "application/json": {
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
            }
        }
    },
}

example_daily_limit_response = {
    "description": "You have reached the daily limit",
    "content": {
        "application/json": {
            "example": {
                "detail": {
                    "daily_limit_per_host": 1,
                    "limit": 1,
                    "host": "www.ecoindex.fr",
                    "latest_result": {
                        "width": 1920,
                        "height": 1080,
                        "size": 107.178,
                        "requests": 6,
                        "score": 87,
                        "water": 1.89,
                        "date": "2023-01-05T12:06:57",
                        "id": "be8c3612-545f-4e72-8880-13b8db74ff6e",
                        "version": 1,
                        "initial_ranking": 1,
                        "url": "https://www.ecoindex.fr",
                        "nodes": 201,
                        "grade": "A",
                        "ges": 1.26,
                        "ecoindex_version": "5.4.1",
                        "page_type": None,
                        "host": "www.ecoindex.fr",
                        "initial_total_results": 1,
                    },
                    "message": (
                        "You have already reached the daily limit of 1 "
                        "requests for host www.ecoindex.fr today"
                    ),
                }
            }
        }
    },
}

example_daily_limit_response = {
    "description": "You have reached the daily limit",
    "content": {
        "application/json": {
            "example": {
                "detail": {
                    "daily_limit_per_host": 1,
                    "limit": 1,
                    "host": "www.ecoindex.fr",
                    "latest_result": {
                        "width": 1920,
                        "height": 1080,
                        "size": 107.178,
                        "requests": 6,
                        "score": 87,
                        "water": 1.89,
                        "date": "2023-01-05T12:06:57",
                        "id": "be8c3612-545f-4e72-8880-13b8db74ff6e",
                        "version": 1,
                        "initial_ranking": 1,
                        "url": "https://www.ecoindex.fr",
                        "nodes": 201,
                        "grade": "A",
                        "ges": 1.26,
                        "ecoindex_version": "5.4.1",
                        "page_type": None,
                        "host": "www.ecoindex.fr",
                        "initial_total_results": 1,
                    },
                    "message": (
                        "You have already reached the daily limit of 1 "
                        "requests for host www.ecoindex.fr today"
                    ),
                }
            }
        }
    },
}

example_host_unreachable = {
    "description": "Host unreachable",
    "content": {
        "application/json": {
            "example": {
                "detail": "The URL http://localhost is unreachable. Are you really sure of this url? 🤔",
            }
        }
    },
}
