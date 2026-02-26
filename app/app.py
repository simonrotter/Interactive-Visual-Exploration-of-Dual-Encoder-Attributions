import os
from PIL import Image
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
from pydantic import BaseModel, Extra

from token_merge import Merge_Type, rule_based_token_converter
from part_of_speech import analyze_pos

from fastapi.responses import FileResponse
import pickle

# python -m uvicorn app:app --host 0.0.0.0 --port 8020

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #allow everything for testing
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"], 
)



#pkl file must be in precomputed directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(script_dir, "image_cache"), exist_ok=True)
pickle_path = os.path.join(script_dir, "precomputed/example_attributions.pkl")
df = pd.read_pickle(pickle_path)


# number of rows in pickle file
@app.get("/api/getItemCount")
async def get_item_count():
    return sum(1 for _ in df.iterrows())

#returns a list of all available texts
@app.get("/api/getTexts")
async def get_texts():
    rows_data = []

    #iterate over each row
    for index, row in df.iterrows():
        text_a = row['text_a']
        text_b = row['text_b']

        if isinstance(text_a, np.ndarray):
            text_a = text_a.tolist()
        if isinstance(text_b, np.ndarray):
            text_b = text_b.tolist()

        row_dict = {
            "index": index,
            "text_a": text_a,
            "text_b": text_b
        }
        rows_data.append(row_dict)
    return rows_data

#gives json of a give pikl file row
@app.get("/api/getAttribution/{row_index}")
async def get_attribs(row_index:int):

    row = df.iloc[row_index]
    text_a = row['text_a']
    text_b = row['text_b']
    tokens_a = row['tokens_a']
    tokens_b = row['tokens_b']
    attributions = row['attribution']

    #convert ndarrays
    if isinstance(tokens_a, np.ndarray):
        tokens_a = tokens_a.tolist()
    if isinstance(tokens_b, np.ndarray):
        tokens_b = tokens_b.tolist()
    if isinstance(text_a, np.ndarray):
        text_a = text_a.tolist()
    if isinstance(text_b, np.ndarray):
        text_b = text_b.tolist()
    if isinstance(attributions, np.ndarray):
        attributions = attributions.tolist()

    return {
        "text_a": text_a,
        "text_b": text_b,
        "tokens_a": tokens_a,
        "tokens_b": tokens_b,
        "attributions": attributions
    }

#gets all the data from the pkl file. can be very big json
@app.get("/api/getAllData")
async def get_all():
    rows_data = []

    for index, row in df.iterrows():
        text_a = row['text_a']
        text_b = row['text_b']
        tokens_a = row['tokens_a']
        tokens_b = row['tokens_b']
        attributions = row['attribution']

        if isinstance(tokens_a, np.ndarray):
            tokens_a = tokens_a.tolist()
        if isinstance(tokens_b, np.ndarray):
            tokens_b = tokens_b.tolist()
        if isinstance(text_a, np.ndarray):
            text_a = text_a.tolist()
        if isinstance(text_b, np.ndarray):
            text_b = text_b.tolist()
        if isinstance(attributions, np.ndarray):
            attributions = attributions.tolist()

        row_dict = {
            "index": index,
            "text_a": text_a,
            "text_b": text_b,
            "tokens_a": tokens_a,
            "tokens_b": tokens_b,
            "attributions": attributions
        }

        rows_data.append(row_dict)
    return rows_data

class MergeRequest(BaseModel):
    tokens_a: List[str]
    tokens_b: List[str]
    attributions: List[List[float]]

    class Config:
        extra = Extra.allow


@app.get("/api/merge-words/{inputId}")
async def merge_tokens(inputId: int):
    pkl_dic = df.iloc[inputId]
    tokens_a = pkl_dic['tokens_a']
    tokens_b = pkl_dic['tokens_b']
    attributions = pkl_dic['attribution']

    #convert ndarrays
    if isinstance(tokens_a, np.ndarray):
        tokens_a = tokens_a.tolist()
    if isinstance(tokens_b, np.ndarray):
        tokens_b = tokens_b.tolist()
    if isinstance(attributions, np.ndarray):
        attributions = attributions.tolist()


    return rule_based_token_converter({
        "tokens_a": tokens_a,
        "tokens_b": tokens_b,
        "attributions": attributions
    }, Merge_Type.Words)

@app.get("/api/merge-word-combinations/{inputId}")
async def merge_combination_tokens(inputId: int):
    pkl_dic = df.iloc[inputId]
    tokens_a = pkl_dic['tokens_a']
    tokens_b = pkl_dic['tokens_b']
    attributions = pkl_dic['attribution']

    #convert ndarrays
    if isinstance(tokens_a, np.ndarray):
        tokens_a = tokens_a.tolist()
    if isinstance(tokens_b, np.ndarray):
        tokens_b = tokens_b.tolist()
    if isinstance(attributions, np.ndarray):
        attributions = attributions.tolist()


    return rule_based_token_converter({
        "tokens_a": tokens_a,
        "tokens_b": tokens_b,
        "attributions": attributions
    }, Merge_Type.Wordcombinations)

@app.get("/api/pos/{inputId}")
async def pos(inputId: int):
    pkl_dic = df.iloc[inputId]
    tokens_a = pkl_dic['tokens_a']
    tokens_b = pkl_dic['tokens_b']
    attributions = pkl_dic['attribution']

    #convert ndarrays
    if isinstance(tokens_a, np.ndarray):
        tokens_a = tokens_a.tolist()
    if isinstance(tokens_b, np.ndarray):
        tokens_b = tokens_b.tolist()
    if isinstance(attributions, np.ndarray):
        attributions = attributions.tolist()


    merged =  rule_based_token_converter({
        "tokens_a": tokens_a,
        "tokens_b": tokens_b,
        "attributions": attributions
    }, Merge_Type.Words)

    return analyze_pos(merged)

@app.get("/api/pos-combinations/{inputId}")
async def pos_combi(inputId: int):
    pkl_dic = df.iloc[inputId]
    tokens_a = pkl_dic['tokens_a']
    tokens_b = pkl_dic['tokens_b']
    attributions = pkl_dic['attribution']

    #convert ndarrays
    if isinstance(tokens_a, np.ndarray):
        tokens_a = tokens_a.tolist()
    if isinstance(tokens_b, np.ndarray):
        tokens_b = tokens_b.tolist()
    if isinstance(attributions, np.ndarray):
        attributions = attributions.tolist()


    merged =  rule_based_token_converter({
        "tokens_a": tokens_a,
        "tokens_b": tokens_b,
        "attributions": attributions
    }, Merge_Type.Wordcombinations)

    return analyze_pos(merged)


#  works on word level
@app.get("/api/attribution-length-stats")
async def get_attribution_length_stats():
    stats = []

    for index, row in df.iterrows():
        tokens_a = row["tokens_a"]
        tokens_b = row["tokens_b"]
        attributions = row["attribution"]

        # Convert if ndarray
        if isinstance(tokens_a, np.ndarray):
            tokens_a = tokens_a.tolist()
        if isinstance(tokens_b, np.ndarray):
            tokens_b = tokens_b.tolist()
        if isinstance(attributions, np.ndarray):
            attributions = attributions.tolist()

        # combine to words
        combined = rule_based_token_converter({
                "tokens_a": tokens_a,
                "tokens_b": tokens_b,
                "attributions": attributions
            }, Merge_Type.Words)

        # Attribution sum over all entries
        flat_attribs = np.array(combined["attributions"]).flatten()
        sum_attribs = float(np.sum(flat_attribs))

        len_a = len(combined["tokens_a"])
        len_b = len(combined["tokens_b"])


        len_ratio = len_a / len_b if len_b != 0 else None

        stats.append({
            "index": index,
            "len_a": len_a,
            "len_b": len_b,
            "length_ratio": len_ratio,
            "sum_attributions": sum_attribs
        })

    return stats


imageAttribs = pickle.load(open('precomputed/clip_attributions.pkl', 'rb'))

@app.get("/imageAttributions/{idx}")
def get_image(idx: int):
    ex = imageAttribs[idx]
    image: Image.Image = ex['image']
    image_path = os.path.join(script_dir, f"image_cache/temp_image_{idx}.png")  # absolute path
    image.save(image_path)

    return analyze_pos({
        "caption": ex['caption'],
        "tokens": ex['tokens'],
        "attributions": np.array(ex['attribution']).tolist(),
        "image_url": f"/image/{idx}"
    })

@app.get("/image/{idx}")
def get_image_file(idx: int):  # also rename this - you had two functions called get_image!
    image_path = os.path.join(script_dir, f"image_cache/temp_image_{idx}.png")
    return FileResponse(image_path, media_type="image/png")

@app.get("/image/{idx}")
def get_image(idx: int):
    image_path = f"image_cache/temp_image_{idx}.png"
    return FileResponse(image_path, media_type="image/png")

@app.get("/imageAttributions")
def get_all_image_attr():
    captions = []
    for index, row in enumerate(imageAttribs):
        row_dict = {
            "index": index,
            "caption": row['caption'],
        }
        captions.append(row_dict)
    return captions

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

DIST_DIR = "dist"

if os.path.exists(DIST_DIR):
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    # Catch-all route to serve Vue's index.html
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_vue(request: Request, full_path: str):
        index_path = os.path.join(DIST_DIR, "index.html")
        with open(index_path) as f:
            return HTMLResponse(content=f.read())
else:
    # Optional: Log a warning so you aren't wondering why the UI is 404ing
    print(f"Warning: '{DIST_DIR}' directory not found. Vue frontend will not be served.")