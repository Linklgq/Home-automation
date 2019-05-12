package com.example.yjf.automation;

import android.app.Application;
import android.content.Context;

import com.example.yjf.automation.api.ApiServiceImpl;
import com.example.yjf.automation.module.ServiceManager;
import com.example.yjf.automation.module.api.ApiService;

public class MainApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        init(getApplicationContext());
    }

    private void init(Context context) {
        ServiceManager.register(ApiService.class,new ApiServiceImpl(context));
    }
}
