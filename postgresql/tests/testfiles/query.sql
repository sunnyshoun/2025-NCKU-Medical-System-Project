SELECT
  u.username,
  u.email,
  u.age,
  u.gender,
  u.job,
  r.name AS role
FROM users u
JOIN user_roles ur ON u.id = ur.userID
JOIN roles r ON ur.roleID = r.roleID
WHERE u.username = 'testuser';
SELECT
  u.username,
  rec.recordID,
  rec.corr_l,
  rec.diopter_l,
  rec.corr_r,
  rec.diopter_r,
  rec.unco_l,
  rec.unco_r,
  rec.createdAt
FROM users u
JOIN records rec ON u.id = rec.userID
WHERE u.username = 'testuser'
ORDER BY rec.createdAt DESC;
SELECT
  u.username,
  r.name AS role
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.userID
LEFT JOIN roles r ON ur.roleID = r.roleID;
SELECT
  u.username,
  rec.recordID,
  rec.unco_l,
  rec.unco_r,
  rec.createdAt
FROM users u
JOIN records rec ON u.id = rec.userID
WHERE rec.createdAt = (
  SELECT MAX(r2.createdAt)
  FROM records r2
  WHERE r2.userID = u.id
);
