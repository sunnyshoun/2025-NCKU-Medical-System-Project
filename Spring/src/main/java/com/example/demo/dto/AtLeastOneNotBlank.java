package com.example.demo.dto;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Constraint(validatedBy = AtLeastOneNotBlankValidator.class)
@Target({ ElementType.TYPE })
@Retention(RetentionPolicy.RUNTIME)
public @interface AtLeastOneNotBlank {

    String message() default "At least one of username or email must be provided";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};

    String[] fields();
}

class AtLeastOneNotBlankValidator implements ConstraintValidator<AtLeastOneNotBlank, Object> {

    private String[] fields;

    @Override
    public void initialize(AtLeastOneNotBlank constraintAnnotation) {
        this.fields = constraintAnnotation.fields();
    }

    @Override
    public boolean isValid(Object object, ConstraintValidatorContext context) {
        try {
            for (String field : fields) {
                Object value = object.getClass().getMethod("get" + capitalize(field)).invoke(object);
                if (value instanceof String str && str != null && !str.trim().isEmpty()) {
                    return true;
                }
            }
            return false;
        } catch (Exception e) {
            return false;
        }
    }

    private String capitalize(String str) {
        if (str == null || str.isEmpty()) {
            return str;
        }
        return str.substring(0, 1).toUpperCase() + str.substring(1);
    }
}