package com.example.yjf.automation.main.operate;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.text.TextUtils;
import android.widget.Button;
import android.widget.Toast;

import com.example.yjf.automation.Constants;
import com.example.yjf.automation.R;
import com.example.yjf.automation.module.ServiceManager;
import com.example.yjf.automation.module.api.ApiResponse;
import com.example.yjf.automation.module.api.ApiService;
import com.example.yjf.automation.utils.EncryptUtil;
import com.example.yjf.automation.utils.LoadingUtil;
import com.google.gson.Gson;

import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.Disposable;

public class OperateActivity extends AppCompatActivity {
    private static final String PREFS_FILE = "prefs_operate";
    private static final String KEY_CNT = "key_cnt";

    private String mPiName;
    private String mPwd;

    private Button mRedBtn;
    private Button mGreenBtn;
    private Button mBlueBtn;
    private PiStatus mPiStatus = new PiStatus();

    private Disposable mDisposable;

    private SharedPreferences mSharedPreferences;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_operate);

        mSharedPreferences = getSharedPreferences(PREFS_FILE, MODE_PRIVATE);
        mPiName = getIntent().getStringExtra(Constants.Extra.PI_NAME);
        mPwd = EncryptUtil.md5(Constants.SALT + getIntent().getStringExtra(Constants.Extra.PWD));
        init();
    }

    private void init() {
        mRedBtn = findViewById(R.id.btn_red);
        mGreenBtn = findViewById(R.id.btn_green);
        mBlueBtn = findViewById(R.id.btn_blue);
        Button send = findViewById(R.id.btn_send_signal);
        Button check = findViewById(R.id.btn_check_status);
        mRedBtn.setOnClickListener(view -> {
            if (TextUtils.equals(mPiStatus.red, PiStatus.ON)) {
                mPiStatus.red = PiStatus.OFF;
                mRedBtn.setBackgroundResource(R.drawable.bg_button_gray_circle_selector);
            } else if (TextUtils.equals(mPiStatus.red, PiStatus.OFF)) {
                mPiStatus.red = PiStatus.ON;
                mRedBtn.setBackgroundResource(R.drawable.bg_button_red_circle_selector);
            }
        });
        mGreenBtn.setOnClickListener(view -> {
            if (TextUtils.equals(mPiStatus.green, PiStatus.ON)) {
                mPiStatus.green = PiStatus.OFF;
                mGreenBtn.setBackgroundResource(R.drawable.bg_button_gray_circle_selector);
            } else if (TextUtils.equals(mPiStatus.green, PiStatus.OFF)) {
                mPiStatus.green = PiStatus.ON;
                mGreenBtn.setBackgroundResource(R.drawable.bg_button_green_circle_selector);
            }
        });
        mBlueBtn.setOnClickListener(view -> {
            if (TextUtils.equals(mPiStatus.blue, PiStatus.ON)) {
                mPiStatus.blue = PiStatus.OFF;
                mBlueBtn.setBackgroundResource(R.drawable.bg_button_gray_circle_selector);
            } else if (TextUtils.equals(mPiStatus.blue, PiStatus.OFF)) {
                mPiStatus.blue = PiStatus.ON;
                mBlueBtn.setBackgroundResource(R.drawable.bg_button_blue_circle_selector);
            }
        });
        send.setOnClickListener(view -> check(true));
        check.setOnClickListener(view -> check(false));

        setButtonColor(mPiStatus);
        check(false);
    }

    private void check(boolean send) {
        LoadingUtil loadingUtil = LoadingUtil.showOn(this);
        loadingUtil.show();

        PiStatus cmd=send?increaseCnt(mPiStatus):null;
        SendRequest request = new SendRequest(mPiName, mPwd, cmd);

        mDisposable = ServiceManager.getService(ApiService.class)
                .doPost(Constants.Path.SEND_SIGNAL, request)
                .observeOn(AndroidSchedulers.mainThread())
                .doFinally(loadingUtil::cancel)
                .subscribe(apiResponse -> {
                    if (apiResponse.ret == ApiResponse.SUCCESS) {
                        mPiStatus = new Gson().fromJson(apiResponse.msg, PiStatus.class);
                        setButtonColor(mPiStatus);
                    } else {
                        Toast.makeText(this, apiResponse.msg, Toast.LENGTH_SHORT).show();
                    }
                }, throwable -> {
                    throwable.printStackTrace();
//                    Toast.makeText(this, getString(R.string.error_network), Toast.LENGTH_SHORT).show();
                    Toast.makeText(this, throwable.getMessage(), Toast.LENGTH_SHORT).show();
                });
    }

    private PiStatus increaseCnt(PiStatus piStatus) {
        int cnt = mSharedPreferences.getInt(KEY_CNT, 0) + 1;
        mSharedPreferences.edit().putInt(KEY_CNT, cnt).apply();
        piStatus.Cnt = cnt;
        return piStatus;
    }

    private void setButtonColor(PiStatus piStatus) {
        if (TextUtils.equals(piStatus.red, PiStatus.ON)) {
            mRedBtn.setBackgroundResource(R.drawable.bg_button_red_circle_selector);
        } else if (TextUtils.equals(piStatus.red, PiStatus.OFF)) {
            mRedBtn.setBackgroundResource(R.drawable.bg_button_gray_circle_selector);
        } else if (TextUtils.equals(piStatus.red, PiStatus.OFFLINE)) {
            mRedBtn.setBackgroundResource(R.drawable.bg_black_circle_shape);
        }

        if (TextUtils.equals(piStatus.green, PiStatus.ON)) {
            mGreenBtn.setBackgroundResource(R.drawable.bg_button_green_circle_selector);
        } else if (TextUtils.equals(piStatus.green, PiStatus.OFF)) {
            mGreenBtn.setBackgroundResource(R.drawable.bg_button_gray_circle_selector);
        } else if (TextUtils.equals(piStatus.green, PiStatus.OFFLINE)) {
            mGreenBtn.setBackgroundResource(R.drawable.bg_black_circle_shape);
        }

        if (TextUtils.equals(piStatus.blue, PiStatus.ON)) {
            mBlueBtn.setBackgroundResource(R.drawable.bg_button_blue_circle_selector);
        } else if (TextUtils.equals(piStatus.blue, PiStatus.OFF)) {
            mBlueBtn.setBackgroundResource(R.drawable.bg_button_gray_circle_selector);
        } else if (TextUtils.equals(piStatus.blue, PiStatus.OFFLINE)) {
            mBlueBtn.setBackgroundResource(R.drawable.bg_black_circle_shape);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (mDisposable != null && !mDisposable.isDisposed()) {
            mDisposable.dispose();
            mDisposable = null;
        }
    }
}
