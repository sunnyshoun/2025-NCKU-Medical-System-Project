package com.example.demo.filter;

import com.example.demo.model.MyAppUser;
import com.example.demo.repository.MyAppUserRepository;
import com.example.demo.utils.JwtTokenUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Optional;
import java.util.UUID;

@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    @Autowired
    private JwtTokenUtil jwtTokenUtil;

    @Autowired
    private MyAppUserRepository myAppUserRepository;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        final String authHeader = request.getHeader("Authorization");
        String jwt = null;
        String userIdString = null;

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            jwt = authHeader.substring(7);
            try {
                userIdString = jwtTokenUtil.extractUserId(jwt);
            } catch (Exception e) {
                System.err.println("JWT extraction failed: " + e.getMessage());
            }
        }

        if (userIdString != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UUID userId = UUID.fromString(userIdString);

            Optional<MyAppUser> userOptional = myAppUserRepository.findById(userId);

            if (userOptional.isPresent() && jwtTokenUtil.validateToken(jwt)) {
                MyAppUser userDetails = userOptional.get();

                UsernamePasswordAuthenticationToken authenticationToken = new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());
                
                authenticationToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                
                SecurityContextHolder.getContext().setAuthentication(authenticationToken);
                System.out.println("User authenticated: " + userDetails.getUsername());
            } else {
                System.err.println("JWT invalid or user not found for ID: " + userIdString);
            }
        }

        filterChain.doFilter(request, response);
    }
}