package com.example.yjf.automation.main.login;

import android.content.Intent;
import android.os.Bundle;
import android.support.design.widget.TextInputLayout;
import android.support.v7.app.AppCompatActivity;
import android.text.TextUtils;
import android.widget.Button;
import android.widget.Toast;

import com.example.yjf.automation.Constants;
import com.example.yjf.automation.R;
import com.example.yjf.automation.main.operate.OperateActivity;
import com.example.yjf.automation.module.ServiceManager;
import com.example.yjf.automation.module.api.ApiResponse;
import com.example.yjf.automation.module.api.ApiService;
import com.example.yjf.automation.utils.EncryptUtil;
import com.example.yjf.automation.utils.LoadingUtil;

import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.Disposable;

public class LoginActivity extends AppCompatActivity {
    private TextInputLayout mPiNameTxil;
    private TextInputLayout mPwdTxil;
    private Disposable mDisposable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        init();
    }

    private void init() {
        mPiNameTxil = findViewById(R.id.txil_pi_name);
        mPwdTxil = findViewById(R.id.txil_pwd);
        Button login = findViewById(R.id.btn_login);
        login.setOnClickListener(view -> login());
    }

    private void login() {
//        if(mDisposable!=null&&!mDisposable.isDisposed()){
//            mDisposable.dispose();
//        }

        mPiNameTxil.setErrorEnabled(false);
        mPwdTxil.setErrorEnabled(false);
        String piName = mPiNameTxil.getEditText().getText().toString();
        String pwd = mPwdTxil.getEditText().getText().toString();
        boolean toLogin = true;
        if (TextUtils.isEmpty(piName)) {
            toLogin = false;
            mPiNameTxil.setError(getString(R.string.hint_pi_name_empty));
            mPiNameTxil.setErrorEnabled(true);
        }
        if (TextUtils.isEmpty(pwd)) {
            toLogin = false;
            mPwdTxil.setError(getString(R.string.hint_pwd_empty));
            mPwdTxil.setErrorEnabled(true);
        }
        if (!toLogin) {
            return;
        }

        LoadingUtil loadingUtil = LoadingUtil.showOn(this);
        loadingUtil.show();
        pwd = EncryptUtil.md5(Constants.SALT + pwd);
        LoginRequest request = new LoginRequest(piName, pwd);
        mDisposable = ServiceManager.getService(ApiService.class)
                .doPost(Constants.Path.REGISTER, request)
                .observeOn(AndroidSchedulers.mainThread())
                .doFinally(loadingUtil::cancel)
                .subscribe(apiResponse -> {
                    if (apiResponse.ret == ApiResponse.SUCCESS) {
                        Toast.makeText(this, getString(R.string.login_success), Toast.LENGTH_SHORT).show();
                        loginSuccess();
                    } else {
                        Toast.makeText(this, apiResponse.msg, Toast.LENGTH_SHORT).show();
                    }
                }, throwable -> {
                    throwable.printStackTrace();
//                    Toast.makeText(this, getString(R.string.error_network), Toast.LENGTH_SHORT).show();
                    Toast.makeText(this, throwable.getMessage(), Toast.LENGTH_SHORT).show();
                });
    }

    private void loginSuccess() {
        String piName = mPiNameTxil.getEditText().getText().toString();
        String pwd = mPwdTxil.getEditText().getText().toString();
        Intent intent = new Intent(this, OperateActivity.class);
        intent.putExtra(Constants.Extra.PI_NAME, piName);
        intent.putExtra(Constants.Extra.PWD, pwd);
        startActivity(intent);
        finish();
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
