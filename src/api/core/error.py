from fastapi import HTTPException, status

class Errors:
    @staticmethod
    def unauthed_exc():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    @staticmethod
    def notfound_exc(comment):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=comment,
        )
    
    @staticmethod
    def token_expired_exc():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    
    @staticmethod
    def invalid_token_exc(error):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token error: {error}",
        )
    
    @staticmethod
    def user_not_found_exc():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token invalid (user not found)",
        )
    
    @staticmethod
    def inactive_user_exc():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user inactive",
        )

    @staticmethod
    def user_exists_exc():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )