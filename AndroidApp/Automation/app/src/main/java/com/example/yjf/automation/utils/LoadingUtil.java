package com.example.yjf.automation.utils;

import android.app.Activity;
import android.content.Context;
import android.support.annotation.NonNull;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;

import com.example.yjf.automation.R;


public class LoadingUtil {
    public static LoadingUtil showOn(@NonNull Activity activity) {
        FrameLayout frameLayout = activity.findViewById(android.R.id.content);
        return new LoadingUtil(frameLayout);
    }

    private ViewGroup mContainerVg;
    private View mLoadingView;

    private LoadingUtil(ViewGroup container) {
        mContainerVg = container;
    }

    public void show() {
        show(null);
    }

    public void show(String hint) {
        Context context = mContainerVg.getContext();
        mLoadingView = LayoutInflater.from(context).inflate(R.layout.loading_circle, mContainerVg, false);
//        ProgressBar progressBar = mLoadingView.findViewById(R.id.pgb_circle_bar);
//        progressBar.getIndeterminateDrawable().setColorFilter(
//                context.getResources().getColor(R.color.colorAccent),PorterDuff.Mode.SRC_IN);
        if (!TextUtils.isEmpty(hint)) {
            TextView textView = mLoadingView.findViewById(R.id.tv_hint_loading_text);
            textView.setText(hint);
            textView.setVisibility(View.VISIBLE);
        }
        mContainerVg.addView(mLoadingView);
    }

    public void cancel() {
        if (mContainerVg != null) {
            mContainerVg.removeView(mLoadingView);
            mLoadingView = null;
            mContainerVg = null;
        }
    }

    public boolean isShow() {
        return mLoadingView != null;
    }

}
