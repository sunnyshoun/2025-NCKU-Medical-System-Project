package com.example.demo.aspect;

import com.example.demo.annotation.JwtAuth;
import com.example.demo.dto.ApiResponse;
import com.example.demo.model.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.utils.JwtErrorHandler;
import com.example.demo.utils.JwtTokenUtil;
import jakarta.servlet.http.HttpServletRequest;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;

import java.util.Optional;
import java.util.UUID;

@Aspect
@Component
public class JwtAuthAspect {

    @Autowired
    private JwtTokenUtil jwtTokenUtil;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private HttpServletRequest request;

    @Around("@annotation(jwtAuth)")
    public Object validateJwt(ProceedingJoinPoint joinPoint, JwtAuth jwtAuth) throws Throwable {
        String jwt = (String) request.getAttribute("jwt_token");
        if (jwt == null) {
            return JwtErrorHandler.handleMissingTokenError();
        }

        try {
            // 檢查 token 類型
            String requiredTokenType = jwtAuth.tokenType();
            if (!requiredTokenType.isEmpty() && !requiredTokenType.equals(jwtTokenUtil.extractTokenType(jwt))) {
                return JwtErrorHandler.handleInvalidTokenTypeError();
            }

            // 驗證 JWT
            if (!jwtTokenUtil.validateToken(jwt)) {
                return new ResponseEntity<>(ApiResponse.error("無效的 JWT Token"), HttpStatus.UNAUTHORIZED);
            }

            // 提取並查找用戶
            UUID userId = jwtTokenUtil.extractUserIdAsUUID(jwt);
            Optional<User> userOptional = userRepository.findById(userId);
            if (userOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("用戶不存在"), HttpStatus.NOT_FOUND);
            }

            // 設置 Spring Security 上下文
            User userDetails = userOptional.get();
            UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                    userDetails, null, userDetails.getAuthorities());
            authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
            SecurityContextHolder.getContext().setAuthentication(authToken);

            // 可選：設置 current_user 到 request
            request.setAttribute("current_user", userDetails);

            // 執行控制器方法
            return joinPoint.proceed();

        } catch (io.jsonwebtoken.ExpiredJwtException e) {
            return JwtErrorHandler.handleJwtError(e);
        } catch (Exception e) {
            return JwtErrorHandler.handleJwtError(e);
        }
    }
}