package com.example.demo.service;

import com.example.demo.model.JwtId;
import com.example.demo.model.User;
import com.example.demo.repository.JwtIdRepository;
import com.example.demo.utils.JwtTokenUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.UUID;

@Service
public class JwtIdService {

    @Autowired
    private JwtIdRepository jwtIdRepository;

    @Autowired
    private JwtTokenUtil jwtTokenUtil;

    /**
     * 生成並儲存 Refresh Token 的 JTI
     * @param user 用戶實體
     * @return JwtId 儲存的 JTI 記錄
     */
    public String createRefreshToken(User user) {
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
    }

    /**
     * 根據 JTI 查找記錄
     * @param jti JTI 值
     * @return Optional<JwtId>
     */
    public Optional<JwtId> findByJti(String jti) {
        return jwtIdRepository.findByJti(jti);
    }

    /**
     * 刪除指定 JTI（用於登出）
     * @param jti JTI 值
     */
    public void deleteRefreshToken(String jti) {
        jwtIdRepository.deleteByJti(jti);
    }
}