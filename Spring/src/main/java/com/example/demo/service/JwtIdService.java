package com.example.demo.service;

import com.example.demo.model.JwtId;
import com.example.demo.model.User;
import com.example.demo.repository.JwtIdRepository;
import com.example.demo.utils.JwtTokenUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class JwtIdService {

    @Autowired
    private JwtIdRepository jwtIdRepository;

    @Autowired
    private JwtTokenUtils jwtTokenUtil;

    @Transactional
    public String createRefreshToken(User user) {
        try {
            // 生成 Refresh Token
            String token = jwtTokenUtil.generateRefreshToken(user.getId());
            String jti = jwtTokenUtil.extractJti(token);

            // 刪除用戶現有的 JTI（確保單一有效 Refresh Token）
            jwtIdRepository.deleteByUserId(user.getId());

            // 儲存新的 JTI
            JwtId jwtId = new JwtId();
            jwtId.setJti(jti);
            jwtId.setUserId(user.getId());
            jwtIdRepository.save(jwtId);

            return token;
        } catch (Exception e) {
            throw e; // 重新拋出異常，交由控制器處理
        }
    }

    public Optional<JwtId> findByJti(String jti) {
        return jwtIdRepository.findByJti(jti);
    }

    @Transactional
    public void deleteRefreshToken(String jti) {
        jwtIdRepository.deleteByJti(jti);
    }
}