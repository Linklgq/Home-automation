package com.example.yjf.automation.main.operate;

import com.example.yjf.automation.module.api.Entity;

public class PiStatus implements Entity{
    public static final String ON="on";
    public static final String OFF="off";
    public static final String OFFLINE="offline";

    public String red=OFF;
    public String green=OFF;
    public String blue=OFF;
    public int Cnt;
}
