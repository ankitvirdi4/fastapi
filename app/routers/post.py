from sqlalchemy.orm import Session
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from .. import models, schemas, oauth2
from ..database import get_db 
from typing import Optional, List
from sqlalchemy import func

router = APIRouter(prefix= '/posts', tags= ['Posts'])

@router.get("/", response_model= List[schemas.PostOut])
def test_posts(db: Session = Depends(get_db), limit: int = 10, skip: int=0, search: Optional[str]=""):
    posts = db.query(models.Post).filter(models.Post.title.contains(search))
    check_posts = posts.limit(limit).offset(skip).all()
    if not check_posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"You have no posts")

    all_posts= db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(models.Vote, models.Vote.post_id==models.Post.id, isouter= True).group_by(models.Post.id).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()    
    
    return all_posts

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
   # cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING * """, (post.title, post.content, post.published))
   # new_post = cursor.fetchone()
   # conn.commit()
    new_post = models.Post(owner_id= current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post
    
@router.get("/{id}", response_model= schemas.PostOut)
def get_post(id: int, response: Response, db: Session = Depends(get_db)):
    # cursor.execute("""SELECT * from posts WHERE id= %s""", (str(id),))
    # post = cursor.fetchone()
    get_post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(models.Vote, models.Vote.post_id==models.Post.id, isouter= True).group_by(models.Post.id).filter(models.Post.id == id)
    
    post = get_post.first() 
    if not post:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"Post with id: {id} was not found")  

    # if post.owner_id != current_user.id:
    #     raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail=f"Not Authorised to perform requested action")
    return post     

@router.delete("/{id}" , status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING * """, (str(id),))
    #del_post = cursor.fetchone()
    #conn.commit()  
    del_post = db.query(models.Post).filter(models.Post.id == id)

    post = del_post.first()
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"post with ID: {id} does not exist")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail=f"Not Authorised to perform requested action") 

    del_post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}", response_model=schemas.Post)
def update_post(id: int, post: schemas.PostCreate , db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #cursor.execute("""UPDATE posts SET title = %s, content = %s, published= %s WHERE id = %s RETURNING * """, (post.title, post.content, post.published,(str(id,)) ))
    #updated_post=cursor.fetchone()
    #conn.commit() 
    updated_post = db.query(models.Post).filter(models.Post.id == id)
    post_query = updated_post.first() 

    if post_query == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"post with ID: {id} does not exist")

    if post_query.owner_id != current_user.id:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail=f"Not Authorised to perform requested action") 
    
    updated_post.update(post.dict(), synchronize_session= False)
    db.commit()
    return updated_post.first() 