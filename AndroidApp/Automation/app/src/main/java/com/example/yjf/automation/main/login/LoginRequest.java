package com.example.yjf.automation.main.login;

import com.example.yjf.automation.module.api.Entity;

public class LoginRequest implements Entity {
    private String piName;
    private String pwd;

    public LoginRequest(String piName, String pwd) {
        this.piName = piName;
        this.pwd = pwd;
    }
}
