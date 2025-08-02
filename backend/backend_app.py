from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import json

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes so frontend apps from different origins can access the API


#Get storage.json path in a cross-platform way
root_dir = Path(__file__).resolve().parent.parent if "__file__" in globals() else Path.cwd().parent
json_path = root_dir / "storage" / "storage.json"


def read_storage_json() -> list[dict]:
    """Open, read and close the storage.json file to retrieve all posts.
    Args:
        None
    Returns:
        list: The a list of dictionaries containing information about the posts.
    """
    with json_path.open("r", encoding="utf-8") as file:
        posts = json.load(file)
    return posts


def write_storage_json(content: list) -> None:
    """Open, write and close the storage.json file to retrieve all posts.
    Args:
        content(list): The content to be written into the json file.
    Returns:
        None
    """
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(content, file, indent=2)


@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    """Handles fetching all posts (GET) and adding new posts (POST)"""
    posts = read_storage_json()

    if request.method == "GET":
        sort_query = (request.args.get("sort") or "").strip().lower()
        direction_query = (request.args.get("direction") or "").strip().lower()
        # Only sort if both queries are valid
        if sort_query and direction_query:
            if sort_query != "title" and sort_query != "content":
                return jsonify({"error": "Bad Request"}), 400
            if direction_query != "asc" and direction_query != "desc":
                return jsonify({"error": "Bad Request"}), 400

            if sort_query == "title" and direction_query == "asc":
                    sorted_posts = sorted(posts, key=lambda x: x["title"])
            
            if sort_query == "title" and direction_query == "desc":
                sorted_posts = sorted(posts, key=lambda x: x["title"], reverse=True)

            if sort_query == "content" and direction_query == "asc":
                sorted_posts = sorted(posts, key=lambda x: x["content"])

            if sort_query == "content" and direction_query == "desc":
                sorted_posts = sorted(posts, key=lambda x: x["content"], reverse=True)

            # Return a sorted list of posts as JSON
            return jsonify(sorted_posts)


        # Return all blog posts as JSON
        return jsonify(posts)

    if request.method == "POST":
        # Get post data from the client
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({"error": "Invalid data"}), 400

        title = data["title"].strip()
        content = data["content"].strip()
        if not title or not content:
            return jsonify({"error": "Title and content cannot be empty."}), 400

        if posts:
            # Generate next ID
            next_id = max(post["id"] for post in posts) + 1
        else:
            next_id = 1  # start from 1 if no posts yet
        
        new_post = {
            "id": next_id,
            "title": title,
            "content": content
        }
        posts.append(new_post)
        write_storage_json(posts)

        return jsonify(new_post), 201


@app.route('/api/posts/<int:id>', methods=['DELETE', 'PUT'])
def handle_post_by_id(id):
    """Handels deleting a post (DELETE) or updating a post (PUT) """
    posts = read_storage_json()
    if request.method == "DELETE":
        new_posts = []
        found = False

        for post in posts:
            if post.get("id") == id:
                found = True
                continue  # Skip the post to delete
            new_posts.append(post)

        if not found:
            return jsonify({"error": f"Post with id {id} not found."}), 404

        write_storage_json(new_posts)
        return jsonify({"message": f"Post with id {id} has been deleted successfully."}), 200

    if request.method == "PUT":
        # Get update data
        data = request.get_json()
        updated_post = {}
        title = data.get("title", "")
        title = title.strip()
        content = data.get("content", "")
        content = content.strip()

        if not data:
            return jsonify({"error": "Invalid data"}), 400
        # Find the post to update
        for post in posts:
            if post.get("id") == id:
                updated_post = post
                break
        if not updated_post:
            return jsonify({"error": f"No post found with id {id}"}), 404

        # Keep existing field if nothing new was provided
        if not title:
            title = post.get("title")
        if not content:
            content = post.get("content")
        
        updated_post["title"] = title
        updated_post["content"] = content

        write_storage_json(posts)

        return jsonify({"id": f"{id}", "title": f"{title}", "content": f"{content}"})


@app.route('/api/posts/search')
def search_post():
    """Search for posts by title and/or by content (case-insensitive substring match)"""
    title_query = (request.args.get("title") or "").strip().lower()
    content_query = (request.args.get("content") or "").strip().lower()

    # Return empty list if both queries are emtpy
    if not title_query and not content_query:
        return jsonify([])

    posts = read_storage_json()
    filtered_posts = []

    for post in posts:
        title = (post.get("title") or  "").lower()
        content = (post.get("content") or "").lower()

        if title_query and content_query:
            if title_query in title and content_query in content:
                filtered_posts.append(post)
        elif title_query:
            if title_query in title:
                filtered_posts.append(post)
        else:
            if content_query in content:
                filtered_posts.append(post)
        
    return jsonify(filtered_posts)
        


# Ignoring log noise
@app.route("/.well-known/<path:subpath>")
def ignore_well_known(subpath):
    return "", 204

# Run the app if executed directly
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
