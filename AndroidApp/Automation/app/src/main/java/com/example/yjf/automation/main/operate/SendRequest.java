package com.example.yjf.automation.main.operate;

import com.example.yjf.automation.module.api.Entity;

public class SendRequest implements Entity {
    private String piName;
    private String pwd;
    private PiStatus cmd;

    public SendRequest(String piName, String pwd, PiStatus cmd) {
        this.piName = piName;
        this.pwd = pwd;
        this.cmd = cmd;
    }
}
